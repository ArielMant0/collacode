import DM from "./data-manager"
import { deviation, max, mean, range } from "d3"
import { cosine, euclidean, jaccard } from "./metrics"

export function getSet(d) {
    return new Set(d.allTags.map(t => t.id))
}
export function getGroupSet(items) {
    return new Set(items.map(d => d.allTags.map(t => t.id)).flat())
}

export function getDistance(a, b, metric="cosine") {
    switch(metric) {
        case "jaccard": return jaccard(a, b, false)
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

const CLS_OPTIONS = {
    metric: "euclidean",
    minStd: 4,
    maxStd: 2,
    minSize: 5,
    maxSize: 13,
    allTags: true,
    useWeights: false,
    sort: 'asc'
}

export function getItemPairDistance(itemA, itemB, options=CLS_OPTIONS) {
    const opts = Object.assign(Object.assign({}, CLS_OPTIONS), options)
    const allTags = opts.allTags

    const tags = DM.getData("tags_tree", false).map(d => d.id)
    const vecA = makeVectorFromItem(itemA, tags, null, allTags)
    const vecB = makeVectorFromItem(itemB, tags, null, allTags)

    // compute similarity
    return getDistance(vecA, vecB, opts.metric)
}

export function getItemDistances(data, options=CLS_OPTIONS) {
    const opts = Object.assign(Object.assign({}, CLS_OPTIONS), options)
    const metric = opts.metric
    const allTags = opts.allTags
    const useWeights = opts.useWeights

    const n = data.length
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

    // compute pairwise similarity
    data.forEach((d, i) => {
        for (let j = i+1; j < n; ++j) {
            const hasTags = d.allTags.length > 0 && data[j].allTags.length > 0
            pwd[i][j] = hasTags ? getDistance(asvec[i], asvec[j], metric) : Infinity
            pwd[j][i] = pwd[i][j]
        }
    })

    return pwd
}

export function getItemClusters(data, targets=[], options=CLS_OPTIONS) {

    const opts = Object.assign(Object.assign({}, CLS_OPTIONS), options)
    const metric = opts.metric
    const minStd = opts.minStd
    const maxStd = opts.maxStd
    const minSize = opts.minSize
    const maxSize = opts.maxSize
    const allTags = opts.allTags
    const useWeights = opts.useWeights

    const n = data.length
    if (n <= minSize) return null

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

    let mergeMinBase = meanD - minStd*stdD
    let mergeMaxBase = meanD - maxStd*stdD

    let changes = true
    let numNoChanges = 0, maxNumNoChanges = 3
    const maxIter = 30

    for (let iter = 0; iter < maxIter && numNoChanges < maxNumNoChanges; ++iter) {

        changes = false
        indices.sort((a, b) => a.length - b.length)

        const k = indices.length

        const cand = []
        let numMerges = 0

        // for each cluster
        for (let i = 0; i < k; ++i) {
            // find closest cluster
            let bestCls = -1
            let bestMin = Number.MAX_VALUE

            // already merged this cluster
            if (indices[i] === null) continue

            for (let j = 0; j < k; ++j) {
                // same cluster, already merged or too large
                if (i === j || indices[j] === null) continue

                const newSize = indices[i].length + indices[j].length
                if (newSize > maxSize) continue

                const [mind, maxd, _] = getMinMaxMeanDistBetweenClusters(indices[i], indices[j], pwd)

                if (mind <= mergeMinBase && (newSize <= minSize || maxd <= mergeMaxBase)) {
                    if (mind <= bestMin) {
                        bestCls = j
                        bestMin = mind
                    }
                }
            }

            if (bestCls >= 0) {
                cand.push({ index: i, other: bestCls, dist: bestMin })
            }
        }

        cand.sort((a, b) => a.dist - b.dist)
        cand.forEach(d => {
            const i = d.index
            const i2 = d.other
            if (indices[i] !== null && indices[i2] !== null && indices[i].length+indices[i2].length <= maxSize) {
                indices[i] = indices[i].concat(indices[i2])
                indices[i2] = null
                numMerges++
            } else if (indices[i] !== null) {

                let bestCls = -1
                let bestMin = Number.MAX_VALUE

                for (let j = 0; j < k; ++j) {
                    // same cluster or already merged
                    if (i === j || indices[j] === null) continue

                    const newSize = indices[i].length + indices[j].length
                    if (newSize > maxSize) continue

                    const [mind, maxd, _] = getMinMaxMeanDistBetweenClusters(indices[i], indices[j], pwd)
                    if (mind <= mergeMinBase && (newSize <= minSize || maxd <= mergeMaxBase)) {
                        if (mind < bestMin) {
                            bestCls = j
                            bestMin = mind
                        }
                    }
                }

                if (bestCls >= 0) {
                    indices[i] = indices[i].concat(indices[bestCls])
                    indices[bestCls] = null
                    numMerges++
                }
            }
        })

        changes = numMerges > 0
        numNoChanges = changes ? 0 : numNoChanges+1

        indices = indices.filter(list => list !== null && list.length > 0)

        if (mergeMinBase < meanD - stdD) {
            mergeMinBase *= 1.1
        }
        if (mergeMaxBase < meanD) {
            mergeMaxBase *= 1.075
        }
    }

    let numTooSmall = indices.reduce((acc, list) => acc + (list.length < minSize ? 1 : 0), 0)
    numNoChanges = 0

    for (let iter = 0; iter < 20 && numTooSmall > 0; ++iter) {

        const cand = []
        const k = indices.length
        const lastIter = numNoChanges > 1 || iter === maxIter-1
        indices.sort((a, b) => a.length - b.length)

        for (let i = 0; i < indices.length; ++i) {
            if (indices[i] === null) continue

            let bestmin = Number.MAX_VALUE, bestmax = 0, best = -1

            // find the cluster with the best min distance
            for (let j = 0; j < indices.length; ++j) {
                if (i === j || indices[j] === null) continue

                const newSize = indices[i].length + indices[j].length
                if (newSize > maxSize) continue
                const tooSmall = indices[i].length < minSize

                const [mind, maxd, _meand] = getMinMaxMeanDistBetweenClusters(indices[i], indices[j], pwd)
                if (mind < bestmin && (newSize <= minSize || maxd <= mergeMaxBase || (lastIter && tooSmall))) {
                    best = j
                    bestmin = mind
                    bestmax = maxd
                }
            }

            if (best >= 0) {
                cand.push({ index: i, other: best, dist: bestmin, bestMax: bestmax })
            }
        }

        let numMerges = 0

        cand.sort((a, b) => {
            if (a.dist === b.dist) {
                return a.bestMax - b.bestMax
            }
            return a.dist - b.dist
        })

        cand.forEach(d => {
            const i = d.index
            const i2 = d.other

            if (indices[i] !== null && indices[i2] !== null && indices[i].length+indices[i2].length <= maxSize) {
                indices[i] = indices[i].concat(indices[i2])
                indices[i2] = null
                numMerges++
            } else if (indices[i] !== null) {

                let bestCls = -1
                let bestMin = Number.MAX_VALUE

                for (let j = 0; j < k; ++j) {
                    // same cluster or already merged
                    if (i === j || indices[j] === null) continue

                    const newSize = indices[i].length + indices[j].length
                    if (newSize > maxSize) continue
                    const tooSmall = indices[i].length < minSize

                    const [mind, maxd, _] = getMinMaxMeanDistBetweenClusters(indices[i], indices[j], pwd)
                    if (mind <= mergeMinBase && (newSize <= minSize || maxd <= mergeMaxBase || (lastIter && tooSmall))) {
                        if (mind < bestMin) {
                            bestCls = j
                            bestMin = mind
                        }
                    }
                }

                if (bestCls >= 0) {
                    indices[i] = indices[i].concat(indices[bestCls])
                    indices[bestCls] = null
                    numMerges++
                }
            }
        })

        if (mergeMaxBase < meanD) {
            mergeMaxBase *= 1.075
        }

        numNoChanges = numMerges > 0 ? 0 : numNoChanges+1
        indices = indices.filter(list => list !== null && list.length > 0)
        // indices = final
        numTooSmall = indices.reduce((acc, list) => acc + (list.length < minSize ? 1 : 0), 0)
    }


    indices.sort((a, b) => b.length - a.length)

    const targetSet = new Set(targets)
    if (targetSet.size > 0) {
        for (let i = 0; i < indices.length; ++i) {
            indices[i] = indices[i].filter(idx => !targetSet.has(data[idx].id))
        }
    }

    // sort all items in a cluster by their avg distance to each other
    const sortAsc = opts.sort === "asc"
    indices.forEach(list => {
        if (list.length < 2) return
        const meanBetween = {}
        // calculate mean distance to others for each item
        list.forEach((d, j) => {
            meanBetween[d] = 0
            for (let i = 0; i < list.length; ++i) {
                if (i !== j) {
                    meanBetween[d] += pwd[j][i]
                }
            }
            meanBetween[d] = meanBetween[d] / list.length
        })

        list.sort((a, b) => sortAsc ?
            meanBetween[a] - meanBetween[b] :
            meanBetween[b] - meanBetween[a]
        )
    })

    const clusters = indices.map(list => list.map(i => data[i]))

    // console.log(clusters.length)
    // clusters.forEach(list => console.log(list.map(d => d.name)))

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