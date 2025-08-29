import DM from "./data-manager"
import { EVIDENCE_TYPE, OBJECTION_ACTIONS, useApp } from "@/store/app"
import { mediaPath } from "./utility"
import { sortObjByValue } from "./sorting";

export function constructSimilarityGraph(data, attr="") {
    // get similarity data
    const sn = [], sl = []
    const nodeSet = new Set()

    const items = DM.getData("items", false)

    const itemUnique = {}

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
                itemUnique[id] = d.unique_target
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
                itemUnique[oid] = d.unique_item
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

    items.forEach(d => {

        // if (itemIds.includes(d.id)) {
        //     console.log(d.name, itemUnique[d.id])
        //     console.log(sl.filter(dd => (dd.source === d.id || dd.target === d.id) && dd.unique >= 2).length,  ">= 2")
        //     console.log(sl.filter(dd => (dd.source === d.id || dd.target === d.id) && dd.unique >= 3).length,  ">= 3")
        //     console.log(sl.filter(dd => (dd.source === d.id || dd.target === d.id) && dd.unique >= 5).length,  ">= 5")
        //     console.log(sl.filter(dd => (dd.source === d.id || dd.target === d.id) && dd.unique >= 10).length, ">= 10")
        // }

        if (itemUnique[d.id] === undefined) {
            d.crowdRobust = false
        } else {
            d.crowdRobust = itemUnique[d.id] >= 5

            if (d.crowdRobust) {
                const match = sl.filter(dd => dd.source === d.id || dd.target === d.id)
                if (d.crowdRobust) {
                    const m3 = match.filter(dd => dd.unique >= 3)
                    const m5 = match.filter(dd => dd.unique >= 5)
                    d.crowdRobust = m3.length + m5.length >= 5 && m5.length >= 1
                }
            }
        }
    })

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
            tagUnique.set(t.id, Math.max((tagUnique.get(t.id) || 0), sim.unique_clients))
            tagCounts.set(t.id, (tagCounts.get(t.id) || 0) + 1)
            if (!tagItems[t.id]) tagItems[t.id] = []
            tagItems[t.id].push(d.id)
            if (sim.value > sim.count) {
                tagVerySim.set(t.id, (tagVerySim.get(t.id) || 0) + 1)
            }
        })
    })

    // go over all scores and check if very high or very low scores differ from user tags

    const w1 = numCounted < 2 ? 0.0 : 0.1 //(numCounted > 4 ? 0.10 : 0.15)
    const w2 = numCounted < 2 ? 0.0 : 0.25 //(numCounted > 4 ? 0.20 : 0.25)
    const w3 = numCounted < 2 ? 0.5 : 0.9 //(numCounted > 4 ? 0.75 : 0.70)
    const w4 = numCounted < 2 ? 0.5 : 0.7 //(numCounted > 4 ? 0.65 : 0.60)

    const numUsers = cleaned[0].target_id === item.id ?
        cleaned[0].unique_target :
        cleaned[0].unique_item

    const low   = Math.round((numCounted * 0.8 + numUsers * 0.2) * w1)
    const lower = Math.round((numCounted * 0.8 + numUsers * 0.2) * w2)
    const high  = Math.round((numCounted * 0.8 + numUsers * 0.2) * w3)
    const upper = Math.round((numCounted * 0.8 + numUsers * 0.2) * w4)

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
    const allCoders = app.usersCanEdit.map(d => d.id)
    const evs = item.evidence

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
            active: false
        }

        const codersYes = allCoders.filter(uid => usersPerTag[tid] && usersPerTag[tid].includes(uid))
        const codersNo = allCoders.filter(uid => !usersPerTag[tid] || !usersPerTag[tid].includes(uid))

        const score2 = (count * 0.8 + unique * 0.2) + (very > 0 ? Math.min(very, 5) * 0.25 : 0)

        const maxItems = numCounted < 5 ? 1 : numCounted * 0.3
        const minItems = numCounted < 5 ? 2 : numCounted * 0.6

        if (score2 <= lower && count <= maxItems && codersYes.length > 0) {
            obj.type = OBJECTION_ACTIONS.REMOVE
            obj.severity = score2 <= low ? 2 : 1
            obj.users = codersYes
            obj.active = !evs.find(e => e.tag_id === tid && e.type === EVIDENCE_TYPE.POSITIVE)
            obj.explanation = `only ${count} of ${numCounted} (${very} very similar) has this tag`,
            warn.push(obj)
        } else if (score2 >= upper && count >= minItems && codersNo.length > 0) {
            obj.type = OBJECTION_ACTIONS.ADD
            obj.severity = score2 >= high ? 2 : 1
            obj.users = codersNo
            obj.active = !evs.find(e => e.tag_id === tid && e.type === EVIDENCE_TYPE.NEGATIVE)
            obj.explanation = `${count} of ${numCounted} (${very} very similar) has this tag`,
            warn.push(obj)
        }
    })

    warn.sort(sortObjByValue("value", { ascending: false }))

    return warn
}

export function getWarningMatches(warnings, item, tag, user) {
    return warnings.filter(d => {
        if (d.type === OBJECTION_ACTIONS.ADD) return false
        return d.tag_id === tag && d.users.includes(user) &&
            !item.evidence.find(e => e.tag_id === tag && e.type === EVIDENCE_TYPE.POSITIVE)
    })
}

export function updateWarnings(warnings, evidence) {
    warnings.forEach(d => {
        const tt = d.type === OBJECTION_ACTIONS.ADD ?
            EVIDENCE_TYPE.NEGATIVE :
            EVIDENCE_TYPE.POSITIVE

        d.active = !evidence.find(e => e.tag_id === d.tag_id && e.type === tt)
    })
}

export function hasWarnings(item) {
    const app = useApp()
    const active = item.warnings.filter(d => d.active)
    if (app.showAllUsers) {
        return app.activeUserId > 0 && app.activeUser.role != "guest" ?
            item.finalized && active.length > 0 :
            active.length > 0
    }
    return item.finalized && active.length > 0
}

export function couldHaveWarnings(item, severity=null) {
    const app = useApp()
    if (!app.warningsEnabled) return false
    return getWarningSize(item, severity) > 0
}

export function getWarningSize(item, severity=null, allUsers=null) {
    const app = useApp()
    if (!app.warningsEnabled) return 0
    const active = item.warnings.filter(d => d.active)
    allUsers = allUsers !== null ? allUsers: app.showAllUsers
    if (allUsers) {
        return severity ?
            active.reduce((acc, d) => acc + (d.severity === severity ? 1 : 0), 0) :
            active.length
    }

    const uid = app.activeUserId
    if (item.finalized) {
        return active.reduce((acc, d) => {
            const matchS = !severity || d.severity === severity
            const matchU = d.users.includes(uid)
            return acc + (matchS && matchU ? 1 : 0)
        }, 0)
    }

    return active.filter(d => d.users.includes(uid)).length > 0 ? 1 : 0
}

export function getWarningColor(w, force) {
    if (!w) return "none"
    if (w.type === OBJECTION_ACTIONS.ADD) {
        return w.active ? "#de078f" : "none"
    }
    return w.active || force ? "#0300ff" : "none"
}

export function getWarningColorByType(type) {
    return type === OBJECTION_ACTIONS.ADD ? "#de078f" : "#0300ff"
}

export function getEvidencePath(type=EVIDENCE_TYPE.POSITIVE) {
    return type === EVIDENCE_TYPE.POSITIVE ?
        "M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z" :
        "M12,2C17.53,2 22,6.47 22,12C22,17.53 17.53,22 12,22C6.47,22 2,17.53 2,12C2,6.47 6.47,2 12,2M15.59,7L12,10.59L8.41,7L7,8.41L10.59,12L7,15.59L8.41,17L12,13.41L15.59,17L17,15.59L13.41,12L17,8.41L15.59,7Z"
}

export function getWarningPath() {
    return "M21,19V20H3V19L5,17V11C5,7.9 7.03,5.17 10,4.29C10,4.19 10,4.1 10,4A2,2 0 0,1 12,2A2,2 0 0,1 14,4C14,4.1 14,4.19 14,4.29C16.97,5.17 19,7.9 19,11V17L21,19M14,21A2,2 0 0,1 12,23A2,2 0 0,1 10,21"
}