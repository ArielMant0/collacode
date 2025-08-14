import DM from "./data-manager"
import { EVIDENCE_TYPE, OBJECTION_ACTIONS, useApp } from "@/store/app"
import { mediaPath } from "./utility"
import { sortObjByString, sortObjByValue } from "./sorting";
import { max, mean } from "d3";

export function constructSimilarityGraph(data, attr="") {
    // get similarity data
    const sn = [], sl = []
    const nodeSet = new Set()

    const items = DM.getData("items")

    // construct the graph
    data.forEach(d => {
        if (d.unique_clients < 2) return
        const id = Number(d.target_id)
        const oid = Number(d.item_id)

        // add the main node
        if (!nodeSet.has(id)) {
            const obj = { id: id, name: "unknown", teaser: null }
            const it = items.find(d => d.id === id)
            if (it) {
                obj.name = it.name
                obj.teaser = mediaPath("teaser", it.teaser)
            }
            sn.push(obj)
            nodeSet.add(id)
        }

        // add the connected node if not already present
        if (!nodeSet.has(oid)) {
            const obj = { id: oid, name: "unknown", teaser: null }
            const it = items.find(d => d.id === oid)
            if (it) {
                obj.name = it.name
                obj.teaser = mediaPath("teaser", it.teaser)
            }
            sn.push(obj)
            nodeSet.add(oid)
        }


        const ex = sl.find(d => d.source === id && d.target === oid || d.source === oid && d.target === id)

        if (ex) {
            // update existing link
            ex.unique += d.unique_clients
            ex.submissions += d.unique_submissions
            ex.value += d["value"+attr]
            ex.count += d["count"+attr]
        } else {
            // add new link
            sl.push({
                id: sl.length+1,
                source: id,
                target: oid,
                unique: d.unique_clients,
                submissions: d.unique_submissions,
                value: d["value"+attr],
                count: d["count"+attr]
            })
        }
    })

    // res.sort(sortObjByString("name"))
    // res.forEach(d => console.log(d.name, d.value))

    // itemIds.forEach(id => {
    //     console.log(DM.getDataItem("items_name", id))
    //     console.log(sl.filter(d => (d.source === id || d.target === id) && d.unique >= 2).length,  ">= 2")
    //     console.log(sl.filter(d => (d.source === id || d.target === id) && d.unique >= 3).length,  ">= 3")
    //     console.log(sl.filter(d => (d.source === id || d.target === id) && d.unique >= 5).length,  ">= 5")
    //     console.log(sl.filter(d => (d.source === id || d.target === id) && d.unique >= 10).length, ">= 10")
    // })

    return { nodes: sn, links: sl }
}

export function getTagWarnings(item, similarites, data=null) {
    if (similarites.length === 0) return []

    const usersPerTag = {}
    item.tags.forEach(d => {
        if (!usersPerTag[d.tag_id]) {
            usersPerTag[d.tag_id] = []
        }
        usersPerTag[d.tag_id].push(d.created_by)
    })

    const warn = []

    // get similar items
    const ids = new Set(similarites.map(d => d.target_id === item.id ? d.item_id : d.target_id))
    const simItems = data ?
        data.filter(d => ids.has(d.id)) :
        DM.getDataBy("items", d => ids.has(d.id))

    // calculate scores for all tags of similar items
    const tagScores = new Map()
    const tagCounts = new Map()
    const tagUnique = new Map()
    const tagVerySim = new Map()
    const tagItems = {}

    const allTags = DM.getDataBy("tags", d => d.is_leaf === 1)
    allTags.forEach(t => {
        tagScores.set(t.id, 0)
        tagCounts.set(t.id, 0)
        tagUnique.set(t.id, 0)
        tagVerySim.set(t.id, 0)
    })

    const cleaned = similarites.filter(s => {
        const minsub = s.target === item.id ? s.unique_target : s.unique_item
        return s.unique_clients > 1 && s.unique_submissions >= minsub * 0.2
    })
    const numCounted = cleaned.length

    if (numCounted < 3) {
        console.debug("too few items to calculate warnings")
        return []
    }

    // go over all tags this item has and add the similarity value
    simItems.forEach(d => {
        const sim = cleaned.find(dd => dd.item_id === d.id || dd.target_id === d.id)
        if (!sim) return

        d.allTags.forEach(t => {
            tagScores.set(t.id, (tagScores.get(t.id) || 0) + sim.value)
            tagUnique.set(t.id, (tagUnique.get(t.id) || 0) + sim.unique_clients)
            tagCounts.set(t.id, (tagCounts.get(t.id) || 0) + 1)
            if (!tagItems[t.id]) tagItems[t.id] = []
            tagItems[t.id].push(d.id)
            if (sim.value > sim.count) {
                tagVerySim.set(t.id, (tagVerySim.get(t.id) || 0) + 1)
            }
        })
    })

    // go over all scores and check if very high or very low scores differ from user tags

    const w1 = numCounted < 2 ? 0.0 : 0.10 //(numCounted > 4 ? 0.10 : 0.15)
    const w2 = numCounted < 2 ? 0.0 : 0.25 //(numCounted > 4 ? 0.20 : 0.25)
    const w3 = numCounted < 2 ? 0.5 : 0.85 //(numCounted > 4 ? 0.75 : 0.70)
    const w4 = numCounted < 2 ? 0.5 : 0.70 //(numCounted > 4 ? 0.65 : 0.60)

    const numUsers = cleaned[0].target_id === item.id ?
        cleaned[0].unique_target :
        cleaned[0].unique_item

    const low   = Math.round(numCounted * w1 * 0.9 + numUsers * 0.1)
    const lower = Math.round(numCounted * w2 * 0.9 + numUsers * 0.1)
    const high  = Math.round(numCounted * w3 * 0.9 + numUsers * 0.1)
    const upper = Math.round(numCounted * w4 * 0.9 + numUsers * 0.1)

    if (high === low) {
        console.debug("low and high similarity threshold too close")
        return []
    }

    // console.log("    ")
    // console.log(item.name)
    // console.log("num games", numCounted)
    // console.log("num target subs", numUsers)
    // console.log("mean unique clients", mean(cleaned, d => d.unique_clients))
    // console.log("max unique clients", max(cleaned, d => d.unique_clients))
    // console.log("tresholds", low, lower, upper, high)
    // console.log("    ")

    const app = useApp()
    const allCoders = app.users.map(d => d.id)

    tagCounts.forEach((_, tid) => {
        const very = tagVerySim.get(tid)
        const count = tagCounts.get(tid)
        const unique = tagUnique.get(tid)

        const obj = {
            tag_id: tid,
            tag_name: DM.getDataItem("tags_name", tid),
            explanation: "",
            value: tagScores.get(tid),
            count: count,
            unique: tagUnique.get(tid),
            items: tagItems[tid],
        }

        const codersYes = allCoders.filter(uid => usersPerTag[tid] && usersPerTag[tid].includes(uid))
        const codersNo = allCoders.filter(uid => !usersPerTag[tid] || !usersPerTag[tid].includes(uid))

        const score2 = unique + (very > 0 ? Math.min(very, numCounted*0.5) * 0.25 : 0)

        if (score2 <= lower && count <= numCounted*0.3 && codersYes.length > 0) {
            obj.type = OBJECTION_ACTIONS.REMOVE
            obj.severity = score2 <= low ? 2 : 1
            obj.users = codersYes
            obj.explanation = `only ${count} of ${numCounted} (${very} very similar) has this tag`,
            warn.push(obj)
        } else if (score2 >= upper && count >= numCounted*0.6 && codersNo.length > 0) {
            obj.type = OBJECTION_ACTIONS.ADD
            obj.severity = score2 >= high ? 2 : 1
            obj.users = codersNo
            obj.explanation = `${count} of ${numCounted} (${very} very similar) has this tag`,
            warn.push(obj)
        }
    })

    warn.sort(sortObjByValue("value", { ascending: false }))

    return warn
}

export function getWarningColor(w, numEv=0) {
    if (!w) return "none"
    return w.type === OBJECTION_ACTIONS.ADD ?
        "#de078f" :
        numEv === 0 ? "#0300ff" : "none"
}

export function getEvidencePath(type=EVIDENCE_TYPE.POSITIVE) {
    return type === EVIDENCE_TYPE.POSITIVE ?
        "M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z" :
        "M12,2C17.53,2 22,6.47 22,12C22,17.53 17.53,22 12,22C6.47,22 2,17.53 2,12C2,6.47 6.47,2 12,2M15.59,7L12,10.59L8.41,7L7,8.41L10.59,12L7,15.59L8.41,17L12,13.41L15.59,17L17,15.59L13.41,12L17,8.41L15.59,7Z"
}

export function getWarningPath() {
    return "M21,19V20H3V19L5,17V11C5,7.9 7.03,5.17 10,4.29C10,4.19 10,4.1 10,4A2,2 0 0,1 12,2A2,2 0 0,1 14,4C14,4.1 14,4.19 14,4.29C16.97,5.17 19,7.9 19,11V17L21,19M14,21A2,2 0 0,1 12,23A2,2 0 0,1 10,21"
}