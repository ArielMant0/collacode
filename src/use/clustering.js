import { deviation, max, mean, range } from "d3"
import DM from "./data-manager"
import { cosine, euclidean, jaccard } from "./metrics"
import { randomShuffle } from "./random"

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
        case "euclidean":
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
    return getDistance(a, b, metric)
}

export function getAvgSimilarity(items, referent) {
    return items.reduce((acc, d) => acc + getSimilarity(d, referent), 0) / items.length
}

export function getAvgDistance(items, referent) {
    return items.reduce((acc, d) => acc + getDistance(d, referent), 0) / items.length
}

export function makeVectorFromGroup(items, referent, weights=null, allTags=false) {
    let vec = referent.map(() => 0)
    items.forEach(d => vec = addVectors(vec, makeVectorFromItem(d, referent, weights, allTags)))
    return vec.map(d  => d / items.length)
}
export function makeVectorFromItem(d, referent, weights=null, allTags=false) {
    const set = new Set()
    d.allTags.forEach(t => {
        if (allTags) {
            t.path.slice(t.path.length-2).forEach(tid => set.add(tid))
        } else {
            set.add(t.id)
        }
    })
    return makeVectorFromSet(set, referent, weights)
}
export function makeVectorFromSet(set, referent, weights=null) {
    return referent.map((d, i) => set.has(d) ? (weights ? weights[i] : 1) : 0)
}

export function addVectors(a, b) {
    return a.map((v, i) => v + b[i])
}

function weight(v, pow=4) {
    return 1 - v**pow
    // return v <= 0.5 ? 1-(1-(v+0.3))**4 : Math.max(0.1, Math.E ** (-8*(-0.5 + v) ** 2))
    // return Math.max(0.1, Math.E ** (-8*(-0.5 + v) ** 2))
    // return v <= 0.2 ? 1-(1-(v+0.4))**pow : 1 - v**pow
    // return v <= 0.5 ? 1 : 1 - 4*(0.5 - v)**2
    // return 1 - 4*(0.5 - v)**2
}

export function getMinMaxMeanDistBetweenClusters(ca, cb, pwd) {
    let mind = Number.MAX_VALUE, maxd = 0
    let meand = 0
    ca.forEach(da => {
        cb.forEach(db => {
            const d = pwd[da][db]
            meand += d
            if (d < mind) {
                mind = d
            }
            if (d > maxd) {
                maxd = d
            }
        })
    })
    return [mind, maxd, meand / (ca.length*cb.length)]
}

export async function getItemClusters(data, metric="euclidean", minSize=2, allTags=false, useWeights=false) {
    const n = data.length
    if (n <= 5) return null

    const pwd = new Array(n)
    for (let i = 0; i < n; ++i) {
        pwd[i] = new Array(n)
        pwd[i].fill(0)
    }

    const tags = DM.getData("tags_tree", false).map(d => d.id)
    const tagCounts = new Map()
    data.forEach(d => {
        const pset = new Set()
        d.allTags.forEach(t => {
            if (allTags) {
                t.path.slice(t.path.length-2).forEach(tid => {
                    if (!pset.has(tid)) {
                        pset.add(tid)
                        tagCounts.set(tid, (tagCounts.get(tid) || 0) + 1)
                    }
                })
            } else {
                tagCounts.set(t.id, (tagCounts.get(t.id) || 0) + 1)
            }
        })
    })
    const mc = max(tagCounts.values())
    const freq = tags.map(tid => useWeights ? (tagCounts.get(tid) / mc) * weight(tagCounts.get(tid) / mc) : 1)
    const asvec = data.map(d => makeVectorFromItem(d, tags, freq, allTags))
    // const asvec = data.map(d => makeVectorFromItem(d, tags))

    const dists = []
    // compute pairwise similarity
    data.forEach((_, i) => {
        for (let j = i+1; j < n; ++j) {
            pwd[i][j] = getDistance(asvec[i], asvec[j], metric)
            pwd[j][i] = pwd[i][j]
            dists.push(pwd[i][j])
        }
    })

    const meanD = mean(dists)
    const stdD = deviation(dists)

    let indices = range(n).map(i => [i])

    let mergeMinBase = meanD - 3.75*stdD
    let mergeMaxBase = meanD - 1*stdD

    let changes = true

    for (let iter = 0; iter < 20 && changes; ++iter) {

        changes = false
        // indices = randomShuffle(indices)

        const k = indices.length

        const cand = []

        // for each cluster
        for (let i = 0; i < k; ++i) {
            // find closest cluster
            for (let j = i+1; j < k; ++j) {
                const [mind, maxd, _] = getMinMaxMeanDistBetweenClusters(indices[i], indices[j], pwd)
                if (mind <= mergeMinBase && maxd <= mergeMaxBase) { // && (maxd < mad || maxd === mad && mind < mid)) {
                    cand.push({ from: i, to: j, minDistance: mind, maxDistance: maxd })
                }
            }
        }

        cand.sort((a, b) => {
            if (a.maxDistance === b.maxDistance) {
                return Math.abs(a.minDistance - b.minDistance)
            }
            return Math.abs(a.maxDistance - b.maxDistance)
        })

        const merged = []
        const taken = new Set()
        let numMerges = 0

        cand.forEach(ca => {
            if (taken.has(ca.from) || taken.has(ca.to)) return
            // merge this cluster into another
            taken.add(ca.from)
            taken.add(ca.to)
            merged.push(indices[ca.from].concat(indices[ca.to]))
            changes = true
            numMerges++
        })


        let single = 0
        // leftover clusters
        indices.forEach((list, i) => {
            single += list.length > 1 ? 0 : 1
            if (!taken.has(i)) {
                taken.add(i)
                merged.push(list)
            }
        })

        indices = merged
        if (mergeMinBase < meanD - stdD) {
            mergeMinBase *= 1.1
        }
        if (mergeMaxBase > meanD + 0.5*stdD) {
            mergeMaxBase *= 0.85
        }
    }

    indices.sort((a, b) => b.length - a.length)
    const clusters = indices.map(list => list.map(i => data[i]))

    const k = clusters.length
    const maxDistances = new Array(k)
    const minDistances = new Array(k)
    const meanDistances = new Array(k)
    for (let i = 0; i < k; ++i) {
        maxDistances[i] = new Array(k)
        minDistances[i] = new Array(k)
        meanDistances[i] = new Array(k)
    }

    let maxmax = 0, minmin = 0
    for (let i = 0; i < k; ++i) {
        maxDistances[i][i] = 0
        minDistances[i][i] = 0
        meanDistances[i][i] = 0
        for (let j = i+1; j < k; ++j) {
            const [dmin, dmax, dmean] = getMinMaxMeanDistBetweenClusters(indices[i], indices[j], pwd)
            maxDistances[i][j] = dmax
            maxDistances[j][i] = dmax
            minDistances[i][j] = dmin
            minDistances[j][i] = dmin
            meanDistances[i][j] = dmean
            meanDistances[j][i] = dmean
            if (dmax > maxmax) {
                maxmax = dmax
            }
            if (dmin > minmin) {
                minmin = dmin
            }
        }
    }
    // normalize distances
    for (let i = 0; i < k; ++i) {
        for (let j = i+1; j < k; ++j) {
            maxDistances[i][j] /= maxmax
            maxDistances[j][i] /= maxmax
            minDistances[i][j] /= minmin
            minDistances[j][i] /= minmin
        }
    }

    return {
        indices: indices,
        clusters: clusters,
        size: clusters.map(d => d.length),
        tags: clusters.map(d => makeVectorFromGroup(d, tags, freq, allTags)),
        pwd: pwd,
        maxDistances: maxDistances,
        minDistances: minDistances,
        meanDistances: meanDistances,
        mean: meanD,
        std: stdD,
        max: maxmax,
        min: minmin
    }
}