import { useApp } from "@/store/app";
import DM from "./data-manager";
import { useLoader } from "./loader"
import { format } from "d3";

let count = 0;

export async function loadDatasets() {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/datasets.json");
        return await resp.json();
    }
    const loader = useLoader();
    return loader.get(`datasets`)
}
export async function loadCodesByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/codes.json");
        return await resp.json()
            .then(res => res.filter(d => d.dataset_id === dataset))
    }
    const loader = useLoader();
    return loader.get(`codes/dataset/${dataset}`)
}
export async function loadGamesByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/games.json");
        return await resp.json()
            .then(res => res.filter(d => d.dataset_id === dataset))
    }
    const loader = useLoader();
    return loader.get(`games/dataset/${dataset}`)
}
export async function loadGameExpertiseByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/game_expertise.json");
        return await resp.json();
    }
    const loader = useLoader();
    return loader.get(`game_expertise/dataset/${dataset}`);
}
export async function loadUsersByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/users.json");
        return await resp.json()
            .then(res => res.filter(d => d.dataset_id === dataset))
    }
    const loader = useLoader();
    return loader.get(`users/dataset/${dataset}`)
}
export async function loadTagsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/tags.json");
        const codes = await loadCodesByDataset(dataset)
        const codeSet = new Set(codes.map(d => d.id))
        return await resp.json()
            .then(res => res.filter(d => codeSet.has(d.code_id)))
    }
    const loader = useLoader();
    return loader.get(`tags/dataset/${dataset}`)
}
export async function loadTagsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/tags.json");
        return await resp.json()
            .then(res => res.filter(d => d.code_id === code))
    }
    const loader = useLoader();
    return loader.get(`tags/code/${code}`)
}
export async function loadDataTagsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/datatags.json");
        const codes = await loadCodesByDataset(dataset)
        const codeSet = new Set(codes.map(d => d.id))
        return await resp.json()
            .then(res => res.filter(d => codeSet.has(d.code_id)))
    }
    const loader = useLoader();
    return loader.get(`datatags/dataset/${dataset}`)
}
export async function loadDataTagsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/datatags.json");
        return await resp.json()
            .then(res => res.filter(d => d.code_id === code))
    }
    const loader = useLoader();
    return loader.get(`datatags/code/${code}`)
}
export async function loadEvidenceByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/evidence.json");
        const codes = await loadCodesByDataset(dataset)
        const codeSet = new Set(codes.map(d => d.id))
        return await resp.json()
            .then(res => res.filter(d => codeSet.has(d.code_id)))
    }
    const loader = useLoader();
    return loader.get(`evidence/dataset/${dataset}`)
}
export async function loadEvidenceByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/evidence.json");
        return await resp.json()
            .then(res => res.filter(d => d.code_id === code))
    }
    const loader = useLoader();
    return loader.get(`evidence/code/${code}`)
}
export async function loadTagAssignmentsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/tag_assignments.json");
        const codes = await loadCodesByDataset(dataset)
        const codeSet = new Set(codes.map(d => d.id))
        return await resp.json()
            .then(res => res.filter(d => codeSet.has(d.old_code) && codeSet.has(d.new_code)))
    }
    const loader = useLoader();
    return loader.get(`tag_assignments/dataset/${dataset}`);
}
export async function loadTagAssignmentsByCodes(oldCode, newCode) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/tag_assignments.json");
        return await resp.json()
            .then(res => res.filter(d => d.old_code === oldCode && d.new_code === newCode))
    }
    const loader = useLoader();
    return loader.get(`tag_assignments/old/${oldCode}/new/${newCode}`);
}
export async function loadMemosByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/memos.json");
        return await resp.json();
    }
    const loader = useLoader();
    return loader.get(`memos/dataset/${dataset}`);
}
export async function loadCodeTransitionsByDataset(dataset) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/code_transitions.json");
        const codes = await loadCodesByDataset(dataset)
        const codeSet = new Set(codes.map(d => d.id))
        return await resp.json()
            .then(res => res.filter(d => codeSet.has(d.old_code) && codeSet.has(d.new_code)))
    }
    const loader = useLoader();
    return loader.get(`code_transitions/dataset/${dataset}`);
}
export async function loadExtGroupsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/ext_groups.json");
        return await resp.json()
            .then(res => res.filter(d => d.code_id === code))
    }
    const loader = useLoader();
    return loader.get(`ext_groups/code/${code}`);
}
export async function loadExternalizationsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/externalizations.json");
        const groups = await loadExtGroupsByCode(code)
        const groupSet = new Set(groups.map(d => d.id))
        return await resp.json()
            .then(res => res.filter(d => groupSet.has(d.group_id)))
    }
    const loader = useLoader();
    return loader.get(`externalizations/code/${code}`);
}
export async function loadExtCategoriesByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/ext_categories.json");
        return await resp.json()
            .then(res => res.filter(d => d.code_id === code))
    }
    const loader = useLoader();
    return loader.get(`ext_categories/code/${code}`);
}
export async function loadExtAgreementsByCode(code) {
    const app = useApp()
    if (app.static) {
        const resp = await fetch("data/ext_agreements.json");
        const exts = await loadExternalizationsByCode(code)
        const extSet = new Set(exts.map(d => d.id))
        return await resp.json()
            .then(res => res.filter(d => extSet.has(d.ext_id)))
    }
    const loader = useLoader();
    return loader.get(`ext_agreements/code/${code}`);
}
export async function loadExtConnectionsByCode(code) {
    const app = useApp()
    if (app.static) {
        const [resp1, resp2, resp3] = await Promise.all([
            fetch("data/ext_cat_connections.json"),
            fetch("data/ext_tag_connections.json"),
            fetch("data/ext_ev_connections.json"),
        ]);
        const exts = await loadExternalizationsByCode(code)
        const extSet = new Set(exts.map(d => d.id))
        return await Promise.all([resp1.json(), resp2.json(), resp3.json()])
            .then(([r1, r2, r3]) => {
                return [
                    r1.filter(d => extSet.has(d.ext_id)),
                    r2.filter(d => extSet.has(d.ext_id)),
                    r3.filter(d => extSet.has(d.ext_id)),
                ]
            })
    }
    const loader = useLoader();
    return Promise.all([
        loader.get(`ext_cat_connections/code/${code}`),
        loader.get(`ext_tag_connections/code/${code}`),
        loader.get(`ext_ev_connections/code/${code}`),
    ])
}

export async function addCodes(codes) {
    const app = useApp();
    if (app.ds === null) return;
    const loader = useLoader();
    return loader.post("add/codes", { dataset: app.ds, rows: Array.isArray(codes) ? codes : [codes] })
}
export async function updateCodes(codes) {
    const loader = useLoader();
    return loader.post("update/codes", { rows: Array.isArray(codes) ? codes : [codes] })
}

export async function startCodeTransition(oldCode, newCode) {
    const loader = useLoader();
    return loader.post(`start/codes/transition/old/${oldCode}/new/${newCode}`);
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

export async function addTags(obj) {
    const loader = useLoader();
    return loader.post("add/tags", { rows: Array.isArray(obj) ? obj : [obj] })
}
export async function updateTags(obj) {
    const loader = useLoader();
    return loader.post("update/tags", { rows: Array.isArray(obj) ? obj : [obj]  })
}
export async function deleteTags(ids) {
    const loader = useLoader();
    return loader.post("delete/tags", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function splitTags(obj) {
    const loader = useLoader();
    return loader.post("split/tags", { rows: Array.isArray(obj) ? obj : [obj]  })
}
export async function mergeTags(obj) {
    const loader = useLoader();
    return loader.post("merge/tags", { rows: Array.isArray(obj) ? obj : [obj]  })
}

export async function addTagAssignments(obj) {
    const loader = useLoader();
    return loader.post("add/tag_assignments", { rows: Array.isArray(obj) ? obj : [obj] })
}
export async function updateTagAssignments(obj) {
    const loader = useLoader();
    return loader.post("update/tag_assignments", { rows: Array.isArray(obj) ? obj : [obj] })
}
export async function deleteTagAssignments(ids) {
    const loader = useLoader();
    return loader.post("delete/tag_assignments", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addDataTags(data) {
    const loader = useLoader();
    return loader.post("add/datatags", { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteDataTags(ids) {
    const loader = useLoader();
    return loader.post("delete/datatags", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addEvidence(obj) {
    const loader = useLoader();
    return loader.post("add/evidence", { rows: Array.isArray(obj) ? obj : [obj] })
}
export async function addEvidenceImage(name, imageData) {
    const loader = useLoader();
    return loader.postImage(`image/evidence/${name}`, imageData);
}
export async function updateEvidence(obj) {
    const loader = useLoader();
    return loader.post("update/evidence", { rows: Array.isArray(obj) ? obj : [obj] })
}
export async function deleteEvidence(ids) {
    const loader = useLoader();
    return loader.post("delete/evidence", { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function getSteamFromId(id) {
    const loader = useLoader();
    return loader.get(`import_game/steam/id/${id}`)
}
export async function getSteamFromName(name) {
    const loader = useLoader();
    return loader.get(`import_game/steam/name/${name}`)
}

export async function updateExtGroups(data) {
    const loader = useLoader();
    return loader.post("update/ext_groups", { rows: Array.isArray(data) ? data : [data] })
}

export async function createExternalization(data) {
    const loader = useLoader();
    return loader.post(`add/externalizations`, { rows: Array.isArray(data) ? data : [data] })
}
export async function updateExternalization(data) {
    const loader = useLoader();
    return loader.post(`update/externalizations`, { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteExternalization(ids) {
    const loader = useLoader();
    return loader.post(`delete/externalizations`, { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function createExtCategory(dataset, code, category) {
    const loader = useLoader();
    return loader.post(`add/ext_categories`, {
        dataset: dataset,
        code: code,
        rows: [category]
    })
}
export async function updateExtCategory(data) {
    const loader = useLoader();
    return loader.post(`update/ext_categories`, { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteExtCategories(ids) {
    const loader = useLoader();
    return loader.post(`delete/ext_categories`, { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addExtAgreement(data) {
    const loader = useLoader();
    return loader.post(`add/ext_agreements`, { rows: Array.isArray(data) ? data : [data] })
}
export async function updateExtAgreement(data) {
    const loader = useLoader();
    return loader.post(`update/ext_agreements`, { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteExtAgreement(ids) {
    const loader = useLoader();
    return loader.post(`delete/ext_agreements`, { ids: Array.isArray(ids) ? ids : [ids] })
}

export async function addGameExpertise(data) {
    const loader = useLoader();
    return loader.post(`add/game_expertise`, { rows: Array.isArray(data) ? data : [data] })
}
export async function updateGameExpertise(data) {
    const loader = useLoader();
    return loader.post(`update/game_expertise`, { rows: Array.isArray(data) ? data : [data] })
}
export async function deleteGameExpertise(ids) {
    const loader = useLoader();
    return loader.post(`delete/game_expertise`, { ids: Array.isArray(ids) ? ids : [ids] })
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
