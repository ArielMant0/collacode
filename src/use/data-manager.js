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
        this.ids.clear()
        this.clearFilters();
    }

    clearFilters() {
        const names = Array.from(this.filters.keys())
        this.filters.clear();
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
            const f = this.filters.get(key);
            const ids = new Set();
            data.forEach(d => {
                d._selected = f ? f.matches(d) : false
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

    hasFilter(key) {
        return this.filters.get(key);
    }

    getFilter(key) {
        return this.filters.get(key);
    }

    setFilter(key, attr, values=null, filterType=FILTER_TYPES.VALUE, getValue=null) {

        let f = this.filters.get(key);
        if (values !== null) {
            if (f) {
                if (f.key !== attr) {
                    f = makeFilter(filterType, attr, getValue ? getValue : attr, values)
                } else {
                    f.set(values);
                }
            } else {
                f = makeFilter(filterType, attr, getValue ? getValue : attr, values)
            }
        }

        if (f.empty()) {
            this.removeFilter(key, attr)
        } else {
            this.filters.set(key, f);
            this._storeSelected(key)
            const times = useTimes()
            times.filtered(key)
        }
    }

    toggleFilter(key, attr, values, filterType=FILTER_TYPES.VALUE, getValue=null) {
        let f = this.filters.get(key);
        const times = useTimes()

        if (values !== null) {

            if (f) {
                if (f.key !== attr) {
                    if (attr === "id") {
                        f = makeFilter(filterType, attr, getValue ? getValue : attr, this.getIds(key))
                        f.toggle(values)
                    } else {
                        f = makeFilter(filterType, attr, getValue ? getValue : attr, values)
                    }
                } else {
                    f.toggle(values)
                }
            } else {
                f = makeFilter(filterType, attr, getValue ? getValue : attr, values)
            }
        }

        if (f.empty()) {
            this.removeFilter(key)
        } else {
            this.filters.set(key, f);
            this._storeSelected(key)
            times.filtered(key)
        }
    }

    removeFilter(key) {
        if (this.hasFilter(key)) {
            this.filters.delete(key);
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

    hasFilterData(key) {
        return this.hasFilter(key)
    }

    getFilterData(key) {
        const tmp = this.filters.get(key);
        return tmp ? tmp[attr].getData() : null
    }
}

const DM = new DataManager()

export { DM as default };