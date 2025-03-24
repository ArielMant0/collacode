import DM from "./data-manager";
import { format } from "d3";

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
