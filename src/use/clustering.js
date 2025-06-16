import { deviation, max, mean } from "d3"
import DM from "./data-manager"
import { cosine, euclidean, jaccard } from "./metrics"
import { useLoader } from "./loader"
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
    const BD = meanD - 3 * stdD

    const nn = new Array(n)
    const ns = new Array(n)

    for (let i = 0; i < n; ++i) {
        // for each item/row: find nearest neighbor
        let df = Number.MAX_VALUE, ds = Number.MAX_VALUE
        let of = null, os = null

        for (let j = 0; j < n; ++j) {
            if (j === i) continue

            if (pwd[i][j] <= BD) {
                if (pwd[i][j] < df) {
                    // save as second neighbor before update
                    if (of !== null) {
                        os = of
                        ds = df
                    }
                    df = pwd[i][j]
                    of = j
                } else if (pwd[i][j] < ds) {
                    ds = pwd[i][j]
                    os = j
                }
            }
        }

        if (of !== null) {
            nn[i] = of
        }
        if (os !== null) {
            ns[i] = of
        }
    }

    let indices = []
    let left = new Set([...Array(n).keys()])

    // get pairs of items as cluster start points
    for (let i = 0; i < n; ++i) {
        const pi = nn[i]
        const pj = nn[pi]
        if (!left.has(i) || !left.has(pi)) continue
        // both are closest to each other
        if (pj === i) {
            indices.push([i, pi])
            left.delete(i)
            left.delete(pi)
        } else {
            // compare second best and give pi to the one
            // has has the worse second best neighbor
            const spi = ns[i]
            const spj = ns[pi]
            if (pwd[i][spi] < pwd[pi][spj]) {
                indices.push([pi, spj])
                left.delete(pi)
                left.delete(spj)
            } else {
                indices.push([i, pi])
                left.delete(i)
                left.delete(pi)
            }
        }
    }

    left.forEach(i => indices.push([i]))

    function getMinMaxDistBetweenClusters(ca, cb) {
        let mind = Number.MAX_VALUE, maxd = 0
        ca.forEach(da => {
            cb.forEach(db => {
                const d = getDistance(asvec[da], asvec[db])
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

    let mergeMinBase = BD
    let mergeMaxBase = meanD //BD

    let changes = true

    for (let iter = 0; iter < 5 && changes; ++iter) {

        const k = indices.length
        const mergeMinDist = mergeMinBase
        const mergeMaxDist = mergeMaxBase// * 2 * iter + 1

        const merged = []
        const taken = new Set()

        // for each cluster
        for (let i = 0; i < k; ++i) {
            if (taken.has(i)) continue

            let mid = Number.MAX_VALUE, mad = Number.MAX_VALUE, midx = null
            // find closest cluster
            for (let j = 0; j < k; ++j) {
                if (i === j || taken.has(j)) continue

                const [mind, maxd] = getMinMaxDistBetweenClusters(indices[i], indices[j])
                if (mind <= mergeMinDist && maxd <= mergeMaxDist && (maxd < mad || maxd === mad && mind < mid)) {
                    // console.log(indices[i].map(d => data[d].name), indices[j].map(d => data[d].name))
                    midx = j
                    mid = mind
                    mad = maxd
                }
            }

            if (midx !== null) {
                // merge this cluster into another
                taken.add(i)
                taken.add(midx)
                merged.push(indices[i].concat(indices[midx]))
                changes = true
            } else {
                // kepp as it is
                merged.push(indices[i])
            }
        }

        indices = merged
        mergeMaxBase *= 0.5
    }

    const clusters = indices.map(list => list.map(i => data[i]))

    // clusters.forEach((items, i) => {
    //     console.log("cluster", i, "size", items.length)
    //     console.log(items.map(d => d.name).join(", "))
    // })

    return {
        clusters: clusters,
        size: clusters.map(d => d.length),
        tags: clusters.map(d => makeVectorFromGroup(d, tags, freq, allTags))
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