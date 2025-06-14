import { deviation, mean } from "d3"
import DM from "./data-manager"
import { cosine, euclidean, jaccard } from "./metrics"

export function getSet(d) {
    return new Set(d.allTags.map(t => t.id))
}
export function getGroupSet(items) {
    return new Set(items.map(d => d.allTags.map(t => t.id)).flat())
}

export function getDistance(a, b, metric="cosine") {
    switch(metric) {
        case "jaccard": return jaccard(a, b)
        case "cosine": return cosine(a, b)
        default: return euclidean(a, b)
    }
}

export function getSimilarity(a, b, metric="cosine") {
    if (metric === "jaccard") {
        return 1 - getDistance(a, b, metric)
    }
    if (metric === "cosine") {
        return getDistance(a, b, metric) - 1
    }
    return 0
}

export function getAvgSimilarity(items, referent) {
    return items.reduce((acc, d) => acc + getSimilarity(d, referent), 0) / items.length
}

export function getAvgDistance(items, referent) {
    return items.reduce((acc, d) => acc + getDistance(d, referent), 0) / items.length
}

export function makeVectorFromGroup(items, referent, discrete=false) {
    const counts = new Map()
    items.forEach(d => d.allTags.forEach(t => counts.set(t.id, (counts.get(t.id) || 0) + 1)))
    const keys = Array.from(counts.keys())
    keys.forEach(k => counts.set(k, counts.get(k) / items.length))
    return makeVectorFromMap(counts, referent, discrete)
}
export function makeVectorFromItem(d, referent) {
    return makeVectorFromSet(new Set(d.allTags.map(t => t.id)), referent)
}
export function makeVectorFromSet(set, referent) {
    return referent.map(d => set.has(d) ? 1 : 0)
}
export function makeVectorFromMap(map, referent, discrete=false) {
    return referent.map(d => map.has(d) ? (discrete ? 1 : map.get(d)) : 0)
}

export function addVectors(a, b) {
    return a.map((v, i) => v + b[i])
}

export function getItemClusters(data, minSimilarity=0.5, minSize=2, cooling=0.66, heating=1.2) {
    const n = data.length
    if (n <= 5) return null

    const pwd = new Array(n)
    for (let i = 0; i < n; ++i) {
        pwd[i] = new Array(n)
        pwd[i].fill(0)
    }
    const nn = new Array(n)

    const tags = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
    const asvec = data.map(d => makeVectorFromItem(d, tags))

    // compute pairwise similarity
    data.forEach((_, i) => {
        for (let j = i+1; j < n; ++j) {
            pwd[i][j] = getSimilarity(asvec[i], asvec[j])
            pwd[j][i] = pwd[i][j]
        }
        // for each item/row: compute numer of neighbors
        nn[i] = pwd[i].reduce((acc, v) => acc + (v >= minSimilarity ? 1 : 0), 0)
    })

    const indices = [...Array(n).keys()]
    indices.sort((a, b) => nn[b] - nn[a])

    let clusters = []
    let left = new Set([...Array(n).keys()])
    // assign clusters starting with largest neighborhoods
    let iter = 0

    let minSimStart = minSimilarity
    while (iter < 5 && left.size / data.length > 0.1) {
        for (let label = 0; label < n; ++label) {

            const ii = indices[label]
            let additions = true
            let minS = minSimStart
            let starting = [ii]
            let items = []
            const tmpLeft = new Set(left)
            tmpLeft.delete(ii)
            let numCycles = 0

            while (numCycles < 1 && additions) {
                const idx = Array.from(tmpLeft.values()).filter(i => starting.some(j => pwd[j][i] >= minS))
                items = items.concat(idx.map(i => data[i]))
                idx.forEach(i => tmpLeft.delete(i))
                starting = idx
                minS *= heating
                additions = idx.length > 0
                numCycles++
            }

            if (items.length >= minSize) {
                clusters.push(items)
                left = tmpLeft
            }
        }
        iter++
        minSimStart *= heating
    }

    let merged = []
    let mergeSim = minSimilarity * heating

    for (let iter = 0; iter < 3; ++iter) {

        merged = []
        const clsVecs = clusters.map(c => makeVectorFromGroup(c, tags))
        const cTaken = new Set()

        // merge clusters that are similar
        const k = clusters.length
        for (let i = 0; i < k; ++i) {
            merged.push(clusters[i])
            const idx = merged.length-1
            for (let j = i+1; j < k; ++j) {
                if (cTaken.has(j)) continue
                const sim = getSimilarity(clsVecs[i], clsVecs[j])
                if (sim >= mergeSim) {
                    cTaken.add(j)
                    merged[idx] = merged[idx].concat(clusters[j])
                    clsVecs[i] = makeVectorFromGroup(merged[idx], tags)
                }
            }
        }

        clusters = merged
        mergeSim *= cooling
    }

    merged.sort((a, b) => b.length - a.length)
    // Array.from(left.values()).forEach(i => merged.push([data[i]]))
    // merged.push(Array.from(left.values()).map(i => data[i]))

    // merged.forEach((items, i) => {
    //     console.log("cluster", i, "size", items.length)
    //     console.log(items.map(d => d.name).join(", "))
    // })

    // return clustering
    return {
        clusters: merged,
        size: merged.map(list => list.length),
        tags: merged.map(list => makeVectorFromGroup(list, tags)),
    }
}