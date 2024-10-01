class DataManager {

    constructor(selKey="games", selAttr="id") {
        this.data = new Map();
        this.filters = new Map();
        this.selKey = selKey;
        this.selAttr = selAttr;
        this.selection = [];
        this.times = {}
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
        this.filters.clear();
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
        this.times[key] = Date.now();
        this.update();
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

    getData(key, filter=true) {
        if (!this.hasData(key)) return [];
        let data = this.data.get(key);
        if (filter && this.hasFilter(key)) {
            const f = this.filters.get(key);
            data = data.filter(d => !Object.entries(f).some(([k, v]) => !this.matches(d, k, v)))
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

    getSelectedIds(key) {
        return this.getData(key, true).map(d => d.id);
    }

    getSize(key, filter=true) {
        return this.getData(key, filter).length;
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
            return !attr || f[attr] !== undefined;
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

    setFilter(key, attr, values) {
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
        } else if (tmp) {
            this.removeFilter(key, attr)
        }
    }

    toggleFilter(key, attr, values) {
        const tmp = this.filters.get(key);
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
            } else {
                console.assert(!Array.isArray(values))
                delete tmp[attr];
            }
            this.filters.set(key, tmp);
        } else {
            const obj = {};
            obj[attr] = Array.isArray(values) ? values : [values];
            this.filters.set(key, obj);
        }

        if (key === this.selKey && attr === this.selAttr) {
            const f = this.filters.get(key);
            this.selection = f ? f[attr] : [];
        }
    }

    removeFilter(key, attr) {
        const tmp = this.filters.get(key);
        if (tmp) {
            delete tmp[attr];

            if (key === this.selKey && attr === this.selAttr) {
                this.selection = [];
            }

            if (Object.keys(tmp) > 0) {
                this.filters.set(key, tmp);
            } else {
                this.filters.delete(key);
            }
        }
    }
}

const DM = new DataManager()

export { DM as default };