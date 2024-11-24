import { useTimes } from "@/store/times";

class DataManager {

    constructor(selKey="games", selAttr="id") {
        this.data = new Map();
        this.filters = new Map();
        this.filterData = new Map();

        this.derived = new Map();
        this.derivedData = new Map();

        this.selKey = selKey;
        this.selAttr = selAttr;
        this.selection = [];
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
        this.clearFilters();
    }

    clearFilters() {
        const names = Array.from(this.filters.keys())
        this.filters.clear();
        const times = useTimes()
        names.forEach(key => times.filtered(key))
        this.update();
    }

    hasSelection() {
        return this.selection.length > 0;
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

    matches(d, key, values) {
        switch(typeof values) {
            case "function":
                return values(d[key]);
            case "object":
                console.assert(Array.isArray(values));
                return values.includes(d[key])
            default:
                return d[key] === values;
        }
    }

    _storeSelected(key) {
        if (this.data.has(key)) {
            const data = this.data.get(key);
            const has = this.hasFilter(key)
            const f = has ? Object.entries(this.filters.get(key)) : [];
            const ids = new Set();
            data.forEach(d => {
                d._selected = has ? !f.some(([k, v]) => !this.matches(d, k, v)) : false
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
            return data.filter(d => d._selected)
        }
        return data
    }

    getDataBy(key, callback) {
        if (!this.hasData(key)) return [];
        return this.data.get(key).filter(callback);
    }

    getDataItem(key, id) {
        if (!this.hasData(key)) return null;
        return this.data.get(key).find(d => d.id === id);
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
        const f = this.filters.get(key);
        if (f) {
            return attr === null && Object.keys(f).length > 0 ||
                attr && f[attr] !== undefined
        }
        return false;
    }

    getFilter(key, attr) {
        const f = this.filters.get(key);
        if (f) {
            return f[attr];
        }
        return null;
    }

    setFilter(key, attr, values, data) {
        const tmp = this.filters.get(key);
        if (values && (!Array.isArray(values) || values.length > 0)) {

            if (key === this.selKey && attr === this.selAttr) {
                this.selection = values;
            }

            if (tmp) {
                tmp[attr] = values;
                this.filters.set(key, tmp);
            } else {
                const obj = {};
                obj[attr] = values;
                this.filters.set(key, obj);
            }

            if (data) {
                const tmp2 = this.filterData.get(key)
                if (tmp2 === undefined) {
                    const obj = {}
                    obj[attr] = data;
                    this.filterData.set(key, obj)
                } else {
                    tmp2[attr] = data;
                    this.filterData.set(key, tmp2)
                }
            }
            this._storeSelected(key)
            const times = useTimes()
            times.filtered(key)
        } else if (tmp) {
            this.removeFilter(key, attr)
        }
    }

    toggleFilter(key, attr, values) {
        const tmp = this.filters.get(key);
        const times = useTimes()

        if (tmp) {
            const vals = tmp[attr];
            if (vals === undefined) {
                tmp[attr] = Array.isArray(values) ? values : [values]
            } else if (Array.isArray(vals)) {
                if (Array.isArray(values)) {
                    values.forEach(v => {
                        const idx = vals.indexOf(v);
                        if (idx >= 0) {
                            vals.splice(idx, 1);
                        } else {
                            vals.push(v);
                        }
                    })
                } else {
                    const idx = vals.indexOf(values);
                    if (idx >= 0) {
                        vals.splice(idx, 1);
                    } else {
                        vals.push(values);
                    }
                }
                // delete if array is empty
                if (vals.length === 0) { delete tmp[attr] }
            } else {
                console.assert(!Array.isArray(values))
                delete tmp[attr];
            }

            if (Object.keys(tmp).length === 0) {
                this.removeFilter(key)
            } else {
                this.filters.set(key, tmp);
                this._storeSelected(key)
                times.filtered(key)
            }
        } else {
            const obj = {};
            obj[attr] = Array.isArray(values) ? values : [values];
            this.filters.set(key, obj);
            this._storeSelected(key)
            times.filtered(key)
        }

        if (key === this.selKey && attr === this.selAttr) {
            const f = this.filters.get(key);
            this.selection = f ? f[attr] : [];
        }
    }

    removeFilter(key, attr) {
        const tmp = this.filters.get(key);
        if (tmp) {
            if (attr && tmp[attr]) {
                delete tmp[attr];
                this.filters.set(key, tmp);
                const tmp2 = this.filterData.get(key)
                if (tmp2) {
                    delete tmp2[attr];
                    this.filterData.set(key, tmp2);
                }
            }

            if (!attr || Object.keys(tmp).length === 0) {
                this.filters.delete(key);
                this.filterData.delete(key)
            }

            if (key === this.selKey && attr === this.selAttr) {
                this.selection = [];
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

    hasFilterData(key, attr) {
        const tmp = this.filterData.get(key);
        return (tmp && attr ? tmp[attr] : tmp) !== undefined
    }

    getFilterData(key, attr) {
        const tmp = this.filterData.get(key);
        return tmp && attr ? tmp[attr] : tmp
    }
}

const DM = new DataManager()

export { DM as default };