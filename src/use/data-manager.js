class DataManager {

    constructor() {
        this.data = new Map();;
        this.update();
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
        console.log(key, data)
        this.data.set(key, data);
        this.update();
    }

    getData(key) {
        return this.data.get(key)
    }

}

const DM = new DataManager()

export { DM as default };