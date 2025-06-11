import DM from "./data-manager"

export function getSet(d) {
    return new Set(d.allTags.map(t => t.id))
}
export function getGroupSet(items) {
    return new Set(items.map(d => d.allTags.map(t => t.id)).flat())
}

export function getSimilarity(a, b) {
    return a.intersection(b).size / a.union(b).size
}

export function getDistance(a, b) {
    return 1 -  getSimilarity(a, b)
}

export function getAvgSimilarity(items, referent) {
    return items.reduce((acc, d) => acc + getSimilarity(d, referent), 0) / items.length
}

export function getAvgDistance(items, referent) {
    return items.reduce((acc, d) => acc + getDistance(d, referent), 0) / items.length
}

export function getItemClusters(maxDistance=0.33, minSize=2, cooling=0.88, heating=1.44) {
    const data = DM.getData("items", false)
    const n = data.length
    if (n <= 10) return new Array(n, 0)

    const pwd = new Array(n)
    for (let i = 0; i < n; ++i) {
        pwd[i] = new Array(n)
        pwd[i].fill(0)
    }
    const nn = new Array(n)

    // compute pairwise distances (jaccard)
    data.forEach((d, i) => {
        const vi = new Set(d.allTags.map(t => t.id))
        for (let j = i+1; j < n; ++j) {
            const vj = new Set(data[j].allTags.map(t => t.id))
            pwd[i][j] = 1 - (vi.intersection(vj).size / vi.union(vj).size)
            pwd[j][i] = pwd[i][j]
        }
        // for each item/row: compute numer of neighbors
        nn[i] = pwd[i].reduce((acc, v) => acc + (v <= maxDistance ? 1 : 0), 0)
    })

    const indices = [...Array(n).keys()]
    indices.sort((a, b) => nn[b] - nn[a])

    const clusters = []
    let left = new Set([...Array(n).keys()])
    // assign clusters starting with largest neighborhoods
    let iter = 0

    let maxDistStart = maxDistance
    while (iter < 3 && left.size / data.length > 0.2) {
        for (let label = 0; label < n; ++label) {

            const ii = indices[label]
            let additions = true
            let maxD = maxDistStart
            let starting = [ii]
            let items = []
            const tmpLeft = new Set(left)
            let numCycles = 0

            while (additions) {
                const idx = Array.from(tmpLeft.values()).filter(i => starting.some(j => pwd[j][i] <= maxD))
                items = items.concat(idx.map(i => data[i]))
                idx.forEach(i => tmpLeft.delete(i))
                starting = idx
                maxD *= cooling
                additions = idx.length > 0
                numCycles++
            }

            if (items.length >= minSize) {
                clusters.push(items)
                left = tmpLeft
            }
        }
        iter++
        maxDistStart *= heating
    }

    const merged = []
    const tagSets = clusters.map(c => {
        const s = new Set()
        c.forEach(d => d.allTags.forEach(t => s.add(t.id)))
        return s
    })

    const cTaken = new Set()
    // merge clusters where centers are similar??
    const k = clusters.length
    for (let i = 0; i < k; ++i) {
        merged.push(clusters[i])
        const idx = merged.length-1
        for (let j = i+1; j < k; ++j) {
            if (cTaken.has(j)) continue
            const int = tagSets[i].intersection(tagSets[j])
            const un = tagSets[i].union(tagSets[j])
            const dist = 1 - (int.size / un.size)
            if (dist <= maxDistance * heating) {
                cTaken.add(j)
                merged[idx] = merged[idx].concat(clusters[j])
                tagSets[i] = un
            }
        }
    }

    merged.sort((a, b) => b.length - a.length)
    // merged.push(Array.from(left.values()).map(i => data[i]))

    // merged.forEach((items, i) => {
    //     console.log("cluster", i, "size", items.length)
    //     console.log(items.map(d => d.name).join(", "))
    // })

    const result = {
        clusters: merged,
        size: merged.map(list => list.length),
        tags: merged.map(list => getGroupSet(list)),
    }
    result.similarity = merged.map((list, i) => getAvgSimilarity(list.map(d => getSet(d)), result.tags[i]))

    // return clustering
    return result
}