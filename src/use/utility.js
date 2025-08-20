import { APP_URLS, useApp } from "@/store/app";
import DM from "./data-manager";
import { format } from "d3";
import { useLoader } from "./loader";

let count = 0;

export function defaultValue(type) {
    switch (type) {
        case "string": return "";
        case "url": return "https://store.steampowered.com/";
        case "integer": return 0;
        case "float": return 0.0;
        case "boolean": return false;
        case "datetime": return new Date();
        case "array": return [];
        case "object": return {};
    }
    return null;
}

export function parseType(d, key, type) {
    if (!d[key]) return;
    try {
        switch (type) {
            case "image": d[key] = ""+d[key]; break;
            case "string": d[key] = ""+d[key]; break;
            case "url": d[key] = d[key]; break;
            case "integer":
                switch(typeof(d[key])) {
                    case 'string': {
                        const l = d[key].toLowerCase()
                        if (l === "true" || l === "false") {
                            d[key] = l === "true" ? 1 : 0
                        } else {
                            d[key] = Number.parseInt(d[key])
                        }
                    } break;
                    case 'boolean':
                        d[key] = d[key] ? 1 : 0
                        break
                    case 'symbol':
                    case 'undefined':
                    case 'object':
                    case 'function':
                        d[key] = NaN
                        break
                }
                break;
            case "float": d[key] = typeof(d[key]) === "number" ? d[key] : Number.parseFloat(d[key]); break;
            case "boolean": d[key] = typeof(d[key]) === "boolean" ? d[key] : (d[key] === true || d[key] === 1 || d[key].match(/true|yes/i) !== null); break;
            case "datetime": d[key] = typeof(d[key]) === "object" ? d[key] :  Date.parse(d[key]); break;
            case "array":
            case "object":
                if (typeof(d[key]) === "string") {
                    try {
                        d[key] = JSON.parse(d[key]);
                    } catch {
                        d[key] = d[key].split(",")
                    }
                }
                break;
        }
    } catch {
        console.error("could not convert field", key, "to", type)
        console.debug(d[key], typeof d[key])
    }
}

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
export function isSteamLink(url) {
    if (!url) {
        return false;
    }
    return url.includes("store.steampowered.com")
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

export function getValue(d, accessor) {
    switch (typeof accessor) {
        case "string":
            return d[accessor]
        case "function":
            return accessor(d)
    }
    return undefined
}

export async function getClipboardContents(dataType="text/") {
    try {
        const clipboardItems = await navigator.clipboard.read();
        for (const clipboardItem of clipboardItems) {
            const imageType = clipboardItem.types.find(type => type.startsWith(dataType))
            if (imageType) {
                const blob = await clipboardItem.getType(imageType)
                return await blobToData(blob)
            }
        }
        return null
    } catch (err) {
        console.error(err.name, err.message);
    }
}

export function blobToData(blob) {
    return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onloadend = () => resolve(reader.result)
        reader.readAsDataURL(blob)
    })
}