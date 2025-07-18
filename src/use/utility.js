import { APP_URLS, useApp } from "@/store/app";
import DM from "./data-manager";
import { format, median, quantile } from "d3";
import { useLoader } from "./loader";
import { sortObjByValue } from "./sorting";

let count = 0;

export function isValidUserName(name) {
    const regex = new RegExp(/^[\w\-\. ]+$/, "gi")
    return regex.test(name)
}
export function isValidUserPassword(name) {
    const regex = new RegExp(/^[\w\-\.\$#&\*\+\,\; ]+$/, "gi")
    return regex.test(name)
}

export function toTreePath(tag, tags) {
    tags = tags ? tags : DM.getData("tags", false);
    let curr = tag;
    const ids = [];
    while (curr) {
        ids.push(curr.id);
        curr = tags.find(d => d.id === curr.parent);
    }
    return ids.reverse();
}

function getSubtreeRec(node, tree, ids) {
    if (node && tree) {
        ids.push(node.id);
        const children = tree.filter(d => d.parent === node.id);
        children.forEach(c => getSubtreeRec(c, tree, ids))
    }
    return ids
}

export function getSubtree(node, tree) {
    tree = tree && typeof tree !== "string" ? tree : DM.getData(tree ? tree : "tags", false);
    const ids = [];
    return getSubtreeRec(node, tree, ids)
}

export function uid(name) {
    return new Id("O-" + (name == null ? "" : name + "-") + ++count);
  }

export class Id {
    constructor(id) {
        this.id = id;
        this.href = new URL(`#${id}`, location) + "";
    }
    toString() {
        return "url(" + this.href + ")";
    }
}

export function formatPath(path) {
    const arr = path.split(" / ")
    return arr.length === 1 ?
        `<b>${arr[0]}</b>` :
        [
            arr.at(0)+"<br/>",
            arr.length === 3 ? "<span class='ml-3'>..</span><br/>" : `<span class='ml-3'>.. (${arr.length-2}x)</span><br/>`,
            `<b class="ml-6">${arr.at(-1)}</b>`
        ].join("")
}
export function formatNumber(number, digits=3) {
    return Number.isInteger(number) && number < 10**digits ? number : format(`.${digits}s`)(number)
}
export function formatStats(number, digits=3) {
    return Number.isInteger(number) && number < 10**digits ? number : format(`,.${digits}r`)(number)
}

export function compareString(a, b) {
    const nameA = a.toLowerCase(); // ignore upper and lowercase
    const nameB = b.toLowerCase(); // ignore upper and lowercase
    if (nameA < nameB) { return -1; }
    if (nameA > nameB) { return 1; }
    // names must be equal
    return 0;
}

export function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); // $& means the whole matched string
}

export function capitalize(string) {
    return string.trim().split(" ").map(d => d.length > 0 ? d[0].toUpperCase()+d.slice(1) : d).join(" ")
}

export function openInNewTab(url) {
    window.open(url, "_blank").focus()
}

export function mediaPath(mediaType, path, dataset=null) {
    const app = useApp()
    const loader = useLoader()
    dataset = dataset !== null ? dataset : app.ds
    let base
    switch (mediaType) {
        case "teaser":
            base = APP_URLS.TEASER + (APP_URLS.TEASER.endsWith("/") ? "" : "/")
            break
        case "evidence":
            base = APP_URLS.EVIDENCE + (APP_URLS.EVIDENCE.endsWith("/") ? "" : "/")
            break
    }
    return loader.url(base + dataset + "/" + path)
}

export function dataPath(dataType, dataset=null) {
    return APP_URLS.DATA +
        (APP_URLS.DATA.endsWith("/") ? "" : "/") +
        (dataset !== null ? dataset + "/"  : "") +
        dataType + ".csv"
}

export function isVideo(path) {
    return path && (
        path.toLowerCase().endsWith("mp4") ||
        path.toLowerCase().endsWith("mov") ||
        path.toLowerCase().endsWith("mkv")
    )
}

export function getTagWarnings(item, similarites, data=null) {
    if (similarites.length === 0) return []

    const app = useApp()
    const tags = new Set(item.allTags.map(d => d.id))

    const warn = []

    // get similar items
    const ids = new Set(similarites.map(d => d.item_id))
    const simItems = data ?
        data.filter(d => ids.has(d.id)) :
        DM.getDataBy("items", d => ids.has(d.id))

    simItems.sort((a, b) => similarites.findIndex(d => d.item_id === a.id) - similarites.findIndex(d => d.item_id === b.id))

    // calculate scores for all tags of similar items
    const tagScores = new Map()
    const tagCounts = new Map()
    const tagItems = {}
    similarites.forEach((d, i) => {
        // go over all tags this item has and add the similarity value
        simItems[i].allTags.forEach(t => {
            tagScores.set(t.id, (tagScores.get(t.id) || 0) + d.count)
            tagCounts.set(t.id, (tagCounts.get(t.id) || 0) + 1)
            if (!tagItems[t.id]) tagItems[t.id] = []
            tagItems[t.id].push(simItems[i].id)
        })
    })

    // go over all scores and check if very high or very low scores differ from user tags
    const scores = Array.from(tagScores.values())
    const low = quantile(scores, 0.1)
    const lower = quantile(scores, 0.2)
    const upper = quantile(scores, 0.8)
    const high = quantile(scores, 0.9)

    tagScores.forEach((score, tid) => {
        const count = tagCounts.get(tid)
        // TODO: set this threshold
        // if (count <= 1) return
        if (score <= lower && tags.has(tid)) {
            warn.push({
                tag_id: tid,
                tag_name: DM.getDataItem("tags_name", tid),
                severity: score <= low ? 2 : 1,
                type: 1,
                explanation: count + " out of " + simItems.length +
                    " similar " + app.itemName + "s have this tag",
                value: score,
                count: count,
                items: tagItems[tid]
            })
        } else if (score >= upper && !tags.has(tid)) {
            warn.push({
                tag_id: tid,
                tag_name: DM.getDataItem("tags_name", tid),
                severity: score >= high ? 2 : 1,
                type: 2,
                explanation: count + " out of " + simItems.length +
                    " similar " + app.itemName + "s have this tag",
                value: score,
                count: count,
                items: tagItems[tid]
            })
        }
    })

    warn.sort(sortObjByValue("value", { ascending: false }))

    return warn
}

export function getWarningPath() {
    return "M21,19V20H3V19L5,17V11C5,7.9 7.03,5.17 10,4.29C10,4.19 10,4.1 10,4A2,2 0 0,1 12,2A2,2 0 0,1 14,4C14,4.1 14,4.19 14,4.29C16.97,5.17 19,7.9 19,11V17L21,19M14,21A2,2 0 0,1 12,23A2,2 0 0,1 10,21"
}

export function getValue(d, accessor) {
    switch (typeof accessor) {
        case "string":
            return d[accessor]
        case "function":
            return accessor(d)
    }
    return undefined
}
