import DM from "./data-manager"
import { OBJECTION_ACTIONS, useApp } from "@/store/app"
import { mediaPath } from "./utility"
import { quantile } from "d3"
import { sortObjByValue } from "./sorting";

export function constructSimilarityGraph(data, attr="") {
    // get similarity data
    const sn = [], sl = []
    const nodeSet = new Set()

    const items = DM.getData("items")

    // construct the graph
    data.forEach(d => {
        if (d.unique < 2) return
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
            ex.unique += d.unique
            ex.value += d["value"+attr]
            ex.count += d["count"+attr]
        } else {
            // add new link
            sl.push({
                id: sl.length+1,
                source: id,
                target: oid,
                unique: d.unique,
                value: d["value"+attr],
                count: d["count"+attr]
            })
        }
    })

    return { nodes: sn, links: sl }
}

export function getTagWarnings(item, similarites, data=null, stats=null) {
    if (similarites.length === 0) return []

    const app = useApp()
    const tags = new Set(item.allTags.map(d => d.id))

    const usersPerTag = {}
    item.tags.forEach(d => {
        if (!usersPerTag[d.tag_id]) {
            usersPerTag[d.tag_id] = []
        }
        usersPerTag[d.tag_id].push(d.created_by)
    })

    const warn = []

    // get similar items
    const ids = new Set(similarites.map(d => d.item_id))
    const simItems = data ?
        data.filter(d => ids.has(d.id)) :
        DM.getDataBy("items", d => ids.has(d.id))

    const indices = new Map(similarites.map((d, i) => ([d.item_id, i])))
    simItems.sort((a, b) => indices.get(a.id) - indices.get(b.id))

    // calculate scores for all tags of similar items
    const tagScores = new Map()
    const tagCounts = new Map()
    const tagUnique = new Map()
    const tagItems = {}

    tags.forEach(tid => {
        tagScores.set(tid, 0)
        tagCounts.set(tid, 0)
        tagUnique.set(tid, 0)
    })

    let numCounted = 0
    let maxUnique = 0, maxCount = 0, maxValue = 0
    let sumCount = 0, sumUnique = 0, sumValue = 0

    const cleaned = similarites.filter(s => s.unique > 1)
    cleaned.forEach(sim => {
        numCounted++
        sumValue += sim.value
        sumCount += sim.count
        sumUnique += sim.unique
        maxValue = Math.max(maxValue, sim.value)
        maxCount = Math.max(maxCount, sim.count)
        maxUnique = Math.max(maxUnique, sim.unique)
    })

    const statObj = {
        name: item.name,
        numTags: item.allTags.length,
        difference: 0,
        percentDifference: 0,
        untagged: 0,
        percentUntagged: 0,
        tagged: 0,
        percentTagged: 0,
        numSimilaritiesCleaned: numCounted,
        numSimilaritiesRaw: similarites.length,
        untaggedTags: [],
        taggedTags: [],
    }

    function addToStats() {
        if (stats !== null) {
            statObj.untagged = statObj.untaggedTags.length
            statObj.percentUntagged = statObj.numTags > 0 ?
                Math.round(statObj.untagged / statObj.numTags * 100) : 0
            statObj.tagged = statObj.taggedTags.length
            statObj.percentTagged = statObj.numTags > 0 ?
                Math.round(statObj.tagged / statObj.numTags * 100) : 0

            statObj.difference = statObj.untagged - statObj.tagged
            statObj.percentDifference = statObj.percentUntagged - statObj.percentTagged
            stats.push(statObj)
        }
    }

    if (cleaned.length < 3 && maxUnique < 3) {
        // addToStats()
        return []
    }

    // go over all tags this item has and add the similarity value
    simItems.forEach(d => {
        const sim = cleaned.find(dd => dd.item_id === d.id)
        if (!sim) return
        d.allTags.forEach(t => {
            tagScores.set(t.id, (tagScores.get(t.id) || 0) + sim.value)
            tagUnique.set(t.id, Math.max((tagUnique.get(t.id) || 0), sim.unique))
            tagCounts.set(t.id, (tagCounts.get(t.id) || 0) + 1)
            if (!tagItems[t.id]) tagItems[t.id] = []
            tagItems[t.id].push(d.id)
        })
    })

    // go over all scores and check if very high or very low scores differ from user tags

    const useScore = false
    const w1 = useScore ? 0.25 : (numCounted > 4 ? 0.10 : 0.15)
    const w2 = useScore ? 0.35 : (numCounted > 4 ? 0.20 : 0.25)
    const w3 = useScore ? 1.30 : (numCounted > 4 ? 0.75 : 0.70)
    const w4 = useScore ? 1.20 : (numCounted > 4 ? 0.65 : 0.60)

    const low   = numCounted * w1
    const lower = Math.max(numCounted * w2, low+1)
    const high  = numCounted * w3
    const upper = Math.min(numCounted * w4, high-1)

    if (high === low || high === low+1) {
        // addToStats()
        console.debug("low and high similarity threshold too close")
        return []
    }

    const which = useScore ? tagScores : tagCounts

    which.forEach((score, tid) => {
        const count = tagCounts.get(tid)

        const obj = {
            tag_id: tid,
            tag_name: DM.getDataItem("tags_name", tid),
            explanation: `${count} of ${numCounted} similar ${app.itemName}s have this tag`,
            value: tagScores.get(tid),
            count: count,
            unique: tagUnique.get(tid),
            items: tagItems[tid],
        }

        if (score >= upper) {
            statObj.untaggedTags.push(obj.tag_name)
        }

        if (score <= lower && tags.has(tid)) {
            obj.type = OBJECTION_ACTIONS.REMOVE
            obj.severity = score <= low ? 2 : 1
            obj.users = usersPerTag[tid]
            statObj.taggedTags.push(obj.tag_name)
            warn.push(obj)
        } else if (score >= upper && !tags.has(tid)) {
            obj.type = OBJECTION_ACTIONS.ADD
            obj.severity = score >= high ? 2 : 1
            obj.users = item.coders.slice()
            statObj.taggedTags.push(obj.tag_name)
            warn.push(obj)
        }
    })

    warn.sort(sortObjByValue("value", { ascending: false }))

    addToStats()

    return warn
}

export function getWarningPath() {
    return "M21,19V20H3V19L5,17V11C5,7.9 7.03,5.17 10,4.29C10,4.19 10,4.1 10,4A2,2 0 0,1 12,2A2,2 0 0,1 14,4C14,4.1 14,4.19 14,4.29C16.97,5.17 19,7.9 19,11V17L21,19M14,21A2,2 0 0,1 12,23A2,2 0 0,1 10,21"
}