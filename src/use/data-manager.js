class DataManager {

    constructor(dataKey="games") {
        this.data = new Map();
        this.filters = new Map();
        this,dataKey = dataKey;
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
        this.update();
    }

    hasSelection() {
        const f = this.filters.get(this.dataKey);
        return f && f.size > 0;
    }

    hasData(key) {
        return this.data.has(key)
    }

    setData(key, data) {
        this.data.set(key, data);
        this.update();
    }

    getData(key, filter=true) {
        let data = this.data.get(key);
        if (filter && this.hasFilter(key)) {
            const f = this.filters.get(key);
            data = data.filter(d => {
                return !Object.entries(f).some(([k, v]) => {
                    switch(typeof v) {
                        case "function":
                            return !v(d[k]);
                        case "object":
                            console.assert(Array.isArray(v));
                            return !v.includes(d[k])
                        default:
                            return d[k] !== v;
                    }
                });
            })
        }
        return data
    }

    getDataBy(key, callback) {
        if (!this.hasData(key)) return [];
        return this.data.get(key).filter(callback);
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

    pushFront(key, datum) {
        const data = this.getData(key);
        if (data) {
            data.unshift(datum)
            this.update();
        }
        return data;
    }

    hasFilter(key) {
        return this.filters.has(key);
    }

    setFilter(key, attr, values) {
        const tmp = this.filters.get(key);
        if (tmp) {
            tmp[attr] = values;
            this.filters.set(key, tmp);
        } else {
            const obj = {};
            obj[attr] = values;
            this.filters.set(key, obj);
        }
    }

    removeFilter(key, attr) {
        const tmp = this.filters.get(key);
        if (tmp) {
            delete tmp[attr];
            this.filters.set(key, tmp);
        }
    }
}

const DM = new DataManager()

export { DM as default };