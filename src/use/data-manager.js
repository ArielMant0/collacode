import { useTimes } from "@/store/times";
import { FILTER_TYPES, makeFilter } from "./filters";

class DataManager {

    constructor() {
        this.data = new Map();
        this.filters = new Map();

        this.derived = new Map();
        this.derivedData = new Map();

        this.times = {}
        this.ids = new Map()
        this.update();
    }

    get empty() {
        return this.data.size === 0;
    }

    update() {
        this.time = Date.now();
    }

    clear() {
        this.data.clear();
        this.derived.clear();
        this.derivedData.clear()
        this.clearFilters();
    }

    clearFilters() {
        const names = Array.from(this.filters.keys())
        this.filters.clear();
        this.ids.clear()
        const times = useTimes()
        names.forEach(key => times.filtered(key))
        this.update();
    }

    hasData(key) {
        return this.data.has(key)
    }

    setData(key, data) {
        this.data.set(key, data);
        const derived = this.getDerivedFor(key)
        derived.forEach(d => this.derivedData.set(d.name, data.map(d.f)))
        this.times[key] = Date.now();
        this.update();
    }

    setDerived(name, key, callback) {
        this.derived.set(name, { key: key, name: name, f: callback })
        if (this.hasData(key)) {
            const data = this.getData(key, false);
            this.derivedData.set(name, data.map(callback))
        }
    }
    getDerived(name) {
        if (this.derivedData.has(name)) {
            return this.derivedData.get(name)
        }
        return []
    }

    getDerivedFor(key) {
        const ds = []
        this.derived.forEach(d => { if (d.key === key) ds.push(d) })
        return ds
    }
    hasDerivedFor(key) {
        let has = false;
        this.derived.forEach(d => has = has || d.key === key);
        return has
    }

    _storeSelected(key) {
        if (this.data.has(key)) {
            const data = this.data.get(key);
            const fils = this.hasFilter(key) ?
                Array.from(this.filters.get(key).values()) :
                null

            const ids = new Set();
            data.forEach(d => {
                d._selected = fils ? fils.every(f => f.matches(d)) : undefined
                if (d._selected) {
                    ids.add(d.id)
                }
            });

            if (ids.size > 0) {
                this.ids.set(key, ids)
            } else {
                this.ids.delete(key)
            }
        }
    }

    getData(key, filter=true) {
        if (!this.hasData(key)) return [];
        const data = this.data.get(key);
        if (filter && this.hasFilter(key)) {
            return this.getDataBy(key, d => d._selected)
        }
        return data
    }

    getDataBy(key, callback) {
        if (!this.hasData(key)) return [];
        const d = this.data.get(key)
        if (d instanceof Map) {
            return Array.from(d.values()).filter(callback)
        }
        return d.filter(callback);
    }

    getDataItem(key, id) {
        if (!this.hasData(key)) return null;
        const d = this.data.get(key)
        if (d instanceof Map) {
            return d.get(id)
        }
        return d.find(dd => dd.id === id);
    }

    getDerivedItem(key, id) {
        if (!this.derived.has(key)) return null;
        const d = this.derivedData.get(key)
        if (d instanceof Map) {
            return d.get(id)
        }
        return d.find(dd => dd.id === id);
    }

    getDataMap(key, callback, filter=true) {
        if (!this.hasData(key)) return [];
        let data = this.data.get(key);
        if (filter && this.hasFilter(key)) {
            data = data.filter(d => d._selected)
        }
        return data.map(callback)
    }

    getSelectedIds(key) {
        return this.getIds(key)
    }
    getSelectedIdsArray(key) {
        return Array.from(this.getSelectedIds(key).values())
    }

    getSize(key, filter=true) {
        if (filter && this.ids.has(key)) {
            return this.ids.get(key).size
        }
        return this.getData(key, false).length;
    }

    getSizeBy(key, callback) {
        return this.getDataBy(key, callback).length;
    }

    find(key, callback) {
        const data = this.getData(key);
        if (data) {
            return data.find(callback)
        }
        return null;
    }

    findDerived(key, callback) {
        const data = this.getDerived(key);
        if (data) {
            return data.find(callback)
        }
        return null;
    }

    push(key, datum) {
        const data = this.getData(key);
        if (data) {
            data.push(datum)
            this.update();
        }
        return data;
    }

    remove(key, id) {
        const data = this.getData(key, false);
        if (data) {
            const index = data.findIndex(d => d.id === id)
            if (index >= 0) {
                data.splice(index, 1);
                this.data.set(key, data)
                return true;
            }
        }
        return false;
    }

    pushFront(key, datum) {
        const data = this.getData(key);
        if (data) {
            data.unshift(datum)
            this.update();
        }
        return data;
    }

    hasFilter(key, attr=null) {
        const fils = this.filters.get(key);
        return attr ? fils.has(attr) : fils !== undefined;
    }

    getFilter(key, attr=null) {
        const fils = this.filters.get(key);
        return attr ? fils.get(attr) : fils
    }

    setFilter(key, attr, values=null, filterType=FILTER_TYPES.VALUE, getValue=null) {

        let fils = this.filters.get(key);
        let f;

        if (values !== null) {
            f = fils ? fils.get(attr) : null
            if (f) {
                if (f.key !== attr || f.type !== filterType) {
                    fils.set(attr, makeFilter(filterType, attr, getValue ? getValue : attr, values))
                } else {
                    f.set(values);
                }
            } else {
                if (!fils) fils = new Map()
                fils.set(attr, makeFilter(filterType, attr, getValue ? getValue : attr, values))
            }
        }

        if (values === null || (f && f.empty())) {
            this.removeFilter(key, attr)
        } else {
            this.filters.set(key, fils);
            this._storeSelected(key)
            const times = useTimes()
            times.filtered(key)
        }
    }

    toggleFilter(key, attr, values, filterType=FILTER_TYPES.VALUE, getValue=null) {
        let fils = this.filters.get(key);
        let f;
        const times = useTimes()

        if (values !== null) {
            f = fils ? fils.get(attr) : null
            if (f) {
                if (f.key !== attr || f.type !== filterType) {
                    if (attr === "id") {
                        const newF = makeFilter(filterType, attr, getValue ? getValue : attr, this.getIds(key))
                        newF.toggle(values)
                        fils.set(attr, newF)
                    } else {
                        fils.set(attr, makeFilter(filterType, attr, getValue ? getValue : attr, values))
                    }
                } else {
                    f.toggle(values)
                }
            } else {
                if (!fils) fils = new Map()
                fils.set(attr, makeFilter(filterType, attr, getValue ? getValue : attr, values))
            }
        }

        if (values === null || (f && f.empty())) {
            this.removeFilter(key, attr)
        } else {
            this.filters.set(key, fils);
            this._storeSelected(key)
            times.filtered(key)
        }
    }

    removeFilter(key, attr=null) {
        if (this.hasFilter(key, attr)) {
            if (attr !== null) {
                const fils = this.filters.get(key)
                fils.delete(attr)
                if (fils.empty()) {
                    this.filters.delete(key);
                } else {
                    this.filters.set(key, fils)
                }
            } else {
                this.filters.delete(key);
            }
            this._storeSelected(key)
            const times = useTimes()
            times.filtered(key)
        }
    }

    getIds(key) {
        if (this.ids.has(key)) {
            return this.ids.get(key)
        }
        return new Set()
    }

    hasFilterData(key, attr=null) {
        return this.hasFilter(key, attr)
    }

    getFilterData(key, attr) {
        const tmp = this.filters.get(key);
        return tmp && attr ? tmp.get(attr).getData() : null
    }
}

const DM = new DataManager()

export { DM as default };
