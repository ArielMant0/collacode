import DM from "./data-manager";
import { useLoader } from "./loader"
import { format } from "d3";

let count = 0;

export function loadDatasets() {
    const loader = useLoader();
    return loader.get(`datasets`)
}
export function loadCodesByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`codes/dataset/${dataset}`)
}
export function loadGamesByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`games/dataset/${dataset}`)
}
export function loadUsersByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`users/dataset/${dataset}`)
}
export function loadTagsByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`tags/dataset/${dataset}`)
}
export function loadTagsByCode(code) {
    const loader = useLoader();
    return loader.get(`tags/code/${code}`)
}
export function loadDataTagsByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`datatags/dataset/${dataset}`)
}
export function loadDataTagsByCode(code) {
    const loader = useLoader();
    return loader.get(`datatags/code/${code}`)
}
export function loadEvidenceByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`evidence/dataset/${dataset}`)
}
export function loadEvidenceByCode(code) {
    const loader = useLoader();
    return loader.get(`evidence/code/${code}`)
}
export function loadTagAssignmentsByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`tag_assignments/dataset/${dataset}`);
}
export function loadTagAssignmentsByCodes(oldCode, newCode) {
    const loader = useLoader();
    return loader.get(`tag_assignments/old/${oldCode}/new/${newCode}`);
}
export function loadMemosByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`memos/dataset/${dataset}`);
}
export function loadCodeTransitionsByDataset(dataset) {
    const loader = useLoader();
    return loader.get(`code_transitions/dataset/${dataset}`);
}

export async function addGames(games, dataset) {
    const loader = useLoader();
    return loader.post("add/games", { rows: games, dataset: dataset });
}
export async function deleteGames(ids) {
    const loader = useLoader();
    return loader.post(`delete/games`, { ids: ids })

}
export async function updateGames(games) {
    const loader = useLoader();
    return loader.post("update/games", { rows: games });
}
export async function addGameTeaser(name, file) {
    const loader = useLoader();
    return loader.postImage(`image/teaser/${name}`, file);
}
export async function updateGameTeaser(item, name, file) {
    const loader = useLoader();
    await loader.postImage(`image/teaser/${name}`, file);
    item.teaserName = name;
    return updateGames([item]);
}
export async function updateGameTags(game, user, code) {

    const loader = useLoader();
    const body = {
        game_id: game.id,
        user_id: user,
        code_id: code,
        created: Date.now(),
    };
    body.tags = game.tags
        .filter(t => t.created_by === user)
        .map(t => {
            if (t.tag_id !== null) {
                return  { tag_id: t.tag_id };
            }
            return { tag_name: t.name, description: t.description }
        })

    return loader.post("update/game/datatags", body)
}

export async function addDataTags(datatags) {
    const loader = useLoader();
    return loader.post("add/datatags", { rows: datatags })
}
export async function deleteDataTags(datatags) {
    const loader = useLoader();
    return loader.post("delete/datatags", { ids: datatags })
}

export async function getSteamFromId(id) {
    const loader = useLoader();
    return loader.get(`import_game/steam/id/${id}`)
}
export async function getSteamFromName(name) {
    const loader = useLoader();
    return loader.get(`import_game/steam/name/${name}`)
}

export function toToTreePath(tag, tags) {
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
    tree = tree ? tree : DM.getData("tags", false);
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

export function formatNumber(number) {
    return format(".2s")(number)
}

export function compareString(a, b) {
    const nameA = a.toLowerCase(); // ignore upper and lowercase
    const nameB = b.toLowerCase(); // ignore upper and lowercase
    if (nameA < nameB) { return -1; }
    if (nameA > nameB) { return 1; }
    // names must be equal
    return 0;
}
