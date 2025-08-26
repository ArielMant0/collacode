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

export function deltaE(rgbA, rgbB) {
    let labA = rgb2lab(rgbA);
    let labB = rgb2lab(rgbB);
    let deltaL = labA[0] - labB[0];
    let deltaA = labA[1] - labB[1];
    let deltaB = labA[2] - labB[2];
    let c1 = Math.sqrt(labA[1] * labA[1] + labA[2] * labA[2]);
    let c2 = Math.sqrt(labB[1] * labB[1] + labB[2] * labB[2]);
    let deltaC = c1 - c2;
    let deltaH = deltaA * deltaA + deltaB * deltaB - deltaC * deltaC;
    deltaH = deltaH < 0 ? 0 : Math.sqrt(deltaH);
    let sc = 1.0 + 0.045 * c1;
    let sh = 1.0 + 0.015 * c1;
    let deltaLKlsl = deltaL / (1.0);
    let deltaCkcsc = deltaC / (sc);
    let deltaHkhsh = deltaH / (sh);
    let i = deltaLKlsl * deltaLKlsl + deltaCkcsc * deltaCkcsc + deltaHkhsh * deltaHkhsh;
    return i < 0 ? 0 : Math.sqrt(i);
}

export function rgb2lab(rgb){
    let r = rgb[0] / 255, g = rgb[1] / 255, b = rgb[2] / 255, x, y, z;
    r = (r > 0.04045) ? Math.pow((r + 0.055) / 1.055, 2.4) : r / 12.92;
    g = (g > 0.04045) ? Math.pow((g + 0.055) / 1.055, 2.4) : g / 12.92;
    b = (b > 0.04045) ? Math.pow((b + 0.055) / 1.055, 2.4) : b / 12.92;
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047;
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 1.00000;
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883;
    x = (x > 0.008856) ? Math.pow(x, 1/3) : (7.787 * x) + 16/116;
    y = (y > 0.008856) ? Math.pow(y, 1/3) : (7.787 * y) + 16/116;
    z = (z > 0.008856) ? Math.pow(z, 1/3) : (7.787 * z) + 16/116;
    return [(116 * y) - 16, 500 * (x - y), 200 * (y - z)]
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