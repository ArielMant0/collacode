class DataManager {

    constructor() {
        this.data = new Map();
        this.filters = new Map();
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
}

const DM = new DataManager()

export { DM as default };