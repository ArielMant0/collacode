import Peer from "peerjs"
import { v4 as uuidv4 } from "uuid"

function sameData(a, b) {
    if (a !== null && b !== null && typeof(a) === "object" && typeof(b) === "object") {
        return Object.keys(a).every(key => a[key] === b[key])
    }
    return a === b
}

export default class Multiplayer {

    constructor(hsData) {
        this.id = Multiplayer.createId()
        this._hs = hsData

        this.peer = new Peer(this.id)
        this.peer.on("connection", conn => {
            if (!this.players.has(conn.peer)) {
                this.connect(conn.peer)
            } else {
                this.send("_players", this.allPlayers)
                this.send("handshake", this.handshakeData)
            }

            conn.on("data", msg => this.receive(msg, conn))
        })

        this.players = new Map()
        this.voting = new Map()
        this.connCallbacks = []
        this.msgCallbacks = {}
        this.voteCallbacks = {}
    }

    static createId() {
        return uuidv4()
    }

    get numPlayers() {
        return this.players.size+1
    }

    get handshakeData() {
        return typeof this._hs === "function" ? this._hs() : this._hs
    }

    get allPlayers() {
        const list = Array.from(this.players.keys())
        list.push(this.id)
        return list
    }

    clear() {
        this.voting.clear()
        this.players.clear()
    }

    reset() {
        this.clear()
        this.connCallbacks = []
        this.msgCallbacks = {}
        this.voteCallbacks = {}
    }

    onConnect(func) {
        this.connCallbacks.push(func)
    }

    disconnect(id) {
        if (this.peer && id !== this.id) {
            this.players.delete(id)
        }
    }

    connect(id) {
        if (this.peer && id !== this.id) {
            const conn = this.peer.connect(id)
            conn.on("open", () => {
                this.players.set(conn.peer, conn)
                this.connCallbacks.forEach(f => f())
                this.send("_players", this.allPlayers)
                this.send("handshake", this.handshakeData)
            });
            this.players.set(id, conn)
        }
    }

    send(name, data) {
        this.players.forEach(conn => conn.send({ type: name, data: data, time: Date.now() }))
    }

    receive(msg, conn) {
        switch(msg.type) {
            case "_players":
                msg.data.forEach(id => {
                    if (!this.players.has(id)) {
                        this.connect(id)
                    }
                })
                break;
            default:
                if (this.msgCallbacks[msg.type]) {
                    this.msgCallbacks[msg.type].forEach(f => f(msg.data, msg.time, conn))
                }
                break;
        }
    }

    onReceive(name, func) {
        if (!this.msgCallbacks[name]) {
            this.msgCallbacks[name] = []
        }
        this.msgCallbacks[name].push(func)
    }

    hasVote(name, id=this.id, data=null) {
        const obj = this.voting.get(name)
        return obj && obj.players.has(id) && sameData(obj.data, data)
    }

    setVote(name, id=this.id, data=null) {
        if (this.voting.has(name)) {
            const obj = this.voting.get(name)
            if (sameData(obj.data, data)) {
                const set = obj.players
                set.add(id)
                // do sth when both players agree
                if (set.size === this.numPlayers) {
                    if (this.voteCallbacks[name]) {
                        this.voteCallbacks[name].forEach(f => f(obj.data))
                    }
                    this.voting.delete(name)
                }
            } else {
                console.error("data not same", data, obj,data)
            }
        } else {
            this.voting.set(name, {
                players: new Set([id]),
                data: data
            })
        }
    }

    onVote(name, func) {
        if (!this.voteCallbacks[name]) {
            this.voteCallbacks[name] = []
        }
        this.voteCallbacks[name].push(func)
    }
}