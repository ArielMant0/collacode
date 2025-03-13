import Peer from "peerjs"

function isSameData(a, b) {
    return a === b
}

export default class Multiplayer {

    constructor(hsData) {
        this.id = null
        this.host = false;
        this._hs = hsData

        this.reconnect()

        this.players = new Map()
        this.voting = new Map()

        this.attempts = new Map()

        this.createCallbacks = []
        this.connCallbacks = []
        this.connErrorCallbacks = []

        this.msgCallbacks = {}
        this.anyVoteCallbacks = []
        this.anyVoteFailCallbacks = []
        this.voteCallbacks = {}
        this.voteUpdateCallbacks = {}
        this.voteFailCallbacks = {}
    }

    get numPlayers() {
        return this.players.size + 1
    }

    get handshakeData() {
        return typeof this._hs === "function" ? this._hs() : this._hs
    }

    get allPlayers() {
        const list = Array.from(this.players.keys())
        list.push(this.id)
        return list
    }

    setHost(host) {
        this.host = host
    }

    clear() {
        this.clearVotes()
        this.players.clear()
    }

    clearVotes() {
        this.voting.clear()
    }

    reset() {
        this.clear()
        this.host = false;
        this.createCallbacks = []
        this.connCallbacks = []
        this.connErrorCallbacks = []
        this.msgCallbacks = {}
        this.anyVoteCallbacks = []
        this.anyVoteFailCallbacks = []
        this.voteCallbacks = {}
        this.voteUpdateCallbacks = {}
        this.voteFailCallbacks = {}
    }

    hasPlayer(id) {
        return this.players.has(id)
    }

    addPlayer(id, conn) {
        this.players.set(id, conn)
        this.connCallbacks.forEach(f => f(id))
        this.sendTo(id, "handshake", this.handshakeData)
        console.debug("added player", id)
    }

    onCreate(func) {
        this.createCallbacks.push(func)
    }

    onConnect(func) {
        this.connCallbacks.push(func)
    }

    onConnectError(func) {
        this.connErrorCallbacks.push(func)
    }

    reconnect() {
        this.peer = new Peer()
        this.peer.on("open", id => this.id = id)
        this.peer.on("connection", conn => {
            console.debug("received connection from", conn.peer)
            if (!this.hasPlayer(conn.peer)) {
                this.addPlayer(conn.peer, conn)
            }
            conn.on("data", msg => this.receive(msg, conn))
            conn.on("error", msg => console.error("multiplayer error", this.id, msg))
        })
    }

    disconnect() {
        if (this.peer) {
            this.peer.destroy()
            this.peer = null;
            this.reconnect()
        }
    }

    disconnectFrom(id) {
        if (this.peer && this.hasPlayer(id)) {
            this.players.delete(id)
        }
    }

    checkConnection(id) {
        if (!this.hasPlayer(id)) {
            console.debug("attempt to connect failed")
            this.connectTo(id)
        } else {
            console.debug("connected successfully")
        }
    }

    connectTo(id, retry=false) {
        if (this.peer && id !== this.id) {
            try {
                const conn = this.peer.connect(id)
                conn.on("open", () => {
                    console.debug("opened connection to", id)
                    if (!this.hasPlayer(id)) {
                        this.addPlayer(id, conn)
                    }
                });
                conn.on("error", msg => console.error("connection error", this.id, msg))
                conn.on("data", msg => console.log("data", this.id, msg))

                console.log(conn)

                if (retry) {
                    setTimeout(() => this.checkConnection(id), 3000)
                 } else {
                    console.error("failed to connect to", id)
                    this.connErrorCallbacks.forEach(f => f(id))
                }
            } catch (e) {
                console.error(e.toString())
            }
        }
    }

    send(name, data) {
        const now = Date.now()
        this.players.forEach(conn => {
            if (conn.open) {
                conn.send({ type: name, data: data, time: now })
                // console.debug("SEND", name, "to", conn.peer, data)
            }
        })
    }

    sendTo(id, name, data) {
        const now = Date.now()
        const p = this.players.get(id)
        if (p) {
            if (p.open) {
                p.send({ type: name, data: data, time: now })
                // console.debug("SEND TO", name, id)
            }
        }
    }

    receive(msg, conn) {
        // console.debug("RECEIVE", msg.type, "from", conn.peer)
        if (this.msgCallbacks[msg.type]) {
            this.msgCallbacks[msg.type].forEach(f => f(msg.data, msg.time, conn))
        }
    }

    onReceive(name, func) {
        if (!this.msgCallbacks[name]) {
            this.msgCallbacks[name] = []
        }
        this.msgCallbacks[name].push(func)
    }

    hasVote(name, id=this.id, dataId=null) {
        const v = this.voting.get(name)
        if (!v) return false
        let has = id ? v.voters.has(id) : true;
        return has && (data ? isSameData(v.dataId, dataId, v.isSame) : true)
    }

    waitingForVote(name) {
        return name ? this.voting.has(name) : this.voting.size > 0
    }

    setVote(name, id, dataId=null, data=null) {
        if (this.voting.has(name)) {
            const obj = this.voting.get(name)
            const set = obj.voters

            if (isSameData(dataId, obj.dataId)) {
                set.add(id)
                // console.debug("VOTE", name, set.size, this.numPlayers)
                if (this.voteUpdateCallbacks[name]) {
                    this.voteUpdateCallbacks[name].forEach(f => f(set))
                }

                // do sth when all players agree
                if (set.size >= this.numPlayers) {
                    this.anyVoteCallbacks.forEach(f => f(name, data))
                    if (this.voteCallbacks[name]) {
                        this.voteCallbacks[name].forEach(f => f(data))
                    }
                    this.voting.delete(name)
                }
            } else {
                console.error("data mismatch", dataId, obj.dataId)
                this.anyVoteFailCallbacks.forEach(f => f(name, data))
                if (this.voteFailCallbacks[name]) {
                    this.voteFailCallbacks[name].forEach(f => f(data))
                }
            }
        } else {
            this.voting.set(name, {
                voters: new Set([id]),
                dataId: dataId,
                data: data,
            })
        }
        return false
    }

    onVote(name, func) {
        if (!this.voteCallbacks[name]) {
            this.voteCallbacks[name] = []
        }
        this.voteCallbacks[name].push(func)
    }

    onVoteUpdate(name, func) {
        if (!this.voteUpdateCallbacks[name]) {
            this.voteUpdateCallbacks[name] = []
        }
        this.voteUpdateCallbacks[name].push(func)
    }

    onVoteFail(name, func) {
        if (!this.voteFailCallbacks[name]) {
            this.voteFailCallbacks[name] = []
        }
        this.voteFailCallbacks[name].push(func)
    }

    onAnyVote(func) {
        this.anyVoteCallbacks.push(func)
    }

    onAnyVoteFail(func) {
        this.anyVoteFailCallbacks.push(func)
    }
}