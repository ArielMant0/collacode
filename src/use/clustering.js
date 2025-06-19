import { deviation, mean, range } from "d3"
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
            t.path.forEach(tid => set.add(tid))
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

function parabola(v) {
    return 1 - v**3
    // return v <= 0.5 ? 1 : 1 - 4*(0.5 - v)**2
    // return 1 - 4*(0.5 - v)**2
}

export async function getItemClusters(data, metric="euclidean", minSize=2, allTags=false) {
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
                t.path.forEach(tid => {
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
    const freq = tags.map(tid => (tagCounts.get(tid) / n) * parabola(tagCounts.get(tid) / n))
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

    function getMinMaxDistBetweenClusters(ca, cb) {
        let mind = Number.MAX_VALUE, maxd = 0
        ca.forEach(da => {
            cb.forEach(db => {
                const d = pwd[da][db]
                if (d < mind) {
                    mind = d
                }
                if (d > maxd) {
                    maxd = d
                }
            })
        })
        return [mind, maxd]
    }

    let mergeMinBase = meanD - 4*stdD
    let mergeMaxBase = meanD - 0.5*stdD

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
                const [mind, maxd] = getMinMaxDistBetweenClusters(indices[i], indices[j])
                if (mind <= mergeMinBase && maxd <= mergeMaxBase) { // && (maxd < mad || maxd === mad && mind < mid)) {
                    cand.push({ from: i, to: j, minDistance: mind, maxDistance: maxd })
                }
            }
        }

        cand.sort((a, b) => {
            if (a.maxDistance === b.maxDistance) {
                return a.minDistance - b.minDistance
            }
            return a.maxDistance - b.maxDistance
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

        // console.log("iteration", iter, "merges", numMerges, single, "single")

        indices = merged
        if (mergeMinBase < meanD - 2*stdD) {
            mergeMinBase *= 1.1
        }
        if (mergeMaxBase > meanD - stdD) {
            mergeMaxBase *= 0.9
        }
    }

    indices.sort((a, b) => b.length - a.length)
    const clusters = indices.map(list => list.map(i => data[i]))

    // console.log(clusters.length, "clusters")

    // clusters.forEach((items, i) => {
    //     console.log("cluster", i, "size", items.length)
    //     console.log(items.map(d => d.name).join(", "))
    // })

    const k = clusters.length
    const maxDistances = new Array(k)
    const minDistances = new Array(k)
    for (let i = 0; i < k; ++i) {
        maxDistances[i] = new Array(k)
        minDistances[i] = new Array(k)
    }

    let maxmax = 0, minmin = 0
    for (let i = 0; i < k; ++i) {
        maxDistances[i][i] = 0
        minDistances[i][i] = 0
        for (let j = i+1; j < k; ++j) {
            const [dmin, dmax] = getMinMaxDistBetweenClusters(indices[i], indices[j])
            maxDistances[i][j] = dmax
            maxDistances[j][i] = dmax
            minDistances[i][j] = dmin
            minDistances[j][i] = dmin
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
            minDistances[i][j] /= maxmax
            minDistances[j][i] /= maxmax
        }
    }

    return {
        clusters: clusters,
        size: clusters.map(d => d.length),
        tags: clusters.map(d => makeVectorFromGroup(d, tags, freq, allTags)),
        maxDistances: maxDistances,
        minDistances: minDistances
    }

    // THIS IS SHIT
    // const loader = useLoader()
    // const res = await loader.post("clustering/hdbscan", { data: asvec })

    // const numClusters = max(res)
    // const clusters = [], size = [], clusterTags = []

    // let dataTmp = data.slice(0)

    // for (let i = 0; i < numClusters; ++i) {
    //     const list = dataTmp.filter((_, j) => res[j] === i)
    //     dataTmp = dataTmp.filter((_, j) => res[j] !== i)
    //     size.push(list.length)
    //     clusterTags.push(makeVectorFromGroup(list, tags, freq, allTags))
    //     clusters.push(list)
    // }

    // clusters.forEach((items, i) => {
    //     console.log("cluster", i, "size", items.length)
    //     console.log(items.map(d => d.name).join(", "))
    // })

    // dataTmp.forEach(d => {
    //     clusters.push([d])
    //     size.push(1)
    //     clusterTags.push(makeVectorFromItem(d, tags, freq, allTags))
    // })

    // return {
    //     clusters: clusters,
    //     size: size,
    //     tags: clusterTags
    // }

    // const indices = [...Array(n).keys()]
    // // indices.sort((a, b) => nn[b] - nn[a])

    // let clusters = []
    // let left = new Set([...Array(n).keys()])
    // // assign clusters starting with largest neighborhoods
    // let iter = 0

    // let maxDistStart = BD
    // while (maxDistStart < MD) {
    //     for (let label = 0; label < n; ++label) {

    //         const ii = indices[label]
    //         let additions = true
    //         let maxD = maxDistStart
    //         let starting = [ii]
    //         let items = []
    //         const tmpLeft = new Set(left)
    //         tmpLeft.delete(ii)
    //         let numCycles = 0

    //         while (additions) {
    //             const idx = Array.from(tmpLeft.values()).filter(i => starting.some(j => pwd[j][i] <= maxD))
    //             items = items.concat(idx.map(i => data[i]))
    //             idx.forEach(i => tmpLeft.delete(i))
    //             starting = idx
    //             maxD -= stdD
    //             additions = idx.length > 0
    //             numCycles++
    //         }

    //         if (items.length >= minSize) {
    //             clusters.push(items)
    //             left = tmpLeft
    //         }
    //     }
    //     iter++
    //     maxDistStart += stdD
    // }

    // let merged = clusters
    // // let merged = []
    // // let mergeDist = BD

    // // Array.from(left.values()).forEach(i => clusters.push([data[i]]))

    // // for (let iter = 0; iter < 5; ++iter) {

    // //     merged = []
    // //     const clsVecs = clusters.map(c => makeVectorFromGroup(c, tags, freq))
    // //     const cTaken = new Set()

    // //     // merge clusters that are similar
    // //     const k = clusters.length
    // //     for (let i = 0; i < k; ++i) {
    // //         merged.push(clusters[i])
    // //         const idx = merged.length-1
    // //         cTaken.add(i)
    // //         for (let j = i+1; j < k; ++j) {
    // //             if (cTaken.has(j) || clusters[i].length+clusters[j].length >= 15) continue
    // //             const dist = getDistance(clsVecs[i], clsVecs[j], metric)
    // //             if (dist <= mergeDist) {
    // //                 cTaken.add(j)
    // //                 merged[idx] = merged[idx].concat(clusters[j])
    // //                 clsVecs[i] = makeVectorFromGroup(merged[idx], tags, freq)
    // //             }
    // //         }
    // //     }

    // //     clusters = merged
    // //     mergeDist -= stdD
    // // }

    // merged.sort((a, b) => b.length - a.length)
    // // Array.from(left.values()).forEach(i => merged.push([data[i]]))
    // // merged.push(Array.from(left.values()).map(i => data[i]))

    // // merged.forEach((items, i) => {
    // //     console.log("cluster", i, "size", items.length)
    // //     console.log(items.map(d => d.name).join(", "))
    // // })

    // // return clustering
    // return {
    //     clusters: merged,
    //     size: merged.map(list => list.length),
    //     tags: merged.map(list => makeVectorFromGroup(list, tags, freq, allTags)),
    // }
}