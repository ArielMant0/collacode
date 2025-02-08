<template>
    <div>
        <div v-for="(o, idx) in options">
            <div class="d-flex align-start">
                <div style="max-width: 25%; min-width: 200px; min-height: 200px;">{{ o }}</div>
                <div style="min-width: 75%; min-height: 200px;" class="d-flex flex-wrap align-start" @drop="e => onDrop(e, idx)" @dragover="allowDrop">
                    <v-sheet v-for="d in byOption.get(idx)"
                        draggable
                        @dragstart="e => onDrag(e, d[itemId])"
                        @click="onClick(d[itemId])"
                        class="cursor-grab mr-1 mb-1 pa-1"
                        :color="selected.has(d[itemId]) ? 'secondary' : 'default'"
                        :key="idx+'_'+d[itemId]"
                        :title="d[itemName]"
                        >
                        <video v-if="isVideo(d)"
                            class="pa-0"
                            :src="imagePrefix+d[itemImage]"
                            loop
                            :autoplay="true"
                            :controls="false"
                            playsinline
                            :width="imageWidth"
                            :height="imageHeight"/>

                        <v-img v-else
                            :cover="!imageFit"
                            :src="d[itemImage] ? imagePrefix+d[itemImage] : imgUrlS"
                            :lazy-src="imgUrlS"
                            :width="imageWidth"
                            :height="imageHeight"/>
                    </v-sheet>
                </div>
            </div>
            <v-divider color="primary" opacity="1" class="mt-2 mb-2"></v-divider>
        </div>
    </div>
</template>

<script setup>
    import { onMounted, reactive, toRaw, watch } from 'vue';
    import imgUrlS from '@/assets/__placeholder__s.png'

    const props = defineProps({
        options: {
            type: Array,
            required: true
        },
        items: {
            type: Array,
            required: true
        },
        initial: { type: Map },
        itemId: {
            type: String,
            default: "id"
        },
        itemName: {
            type: String,
            default: "name"
        },
        itemImage: {
            type: String,
            default: "image"
        },
        imageWidth: {
            type: Number,
            default: 160
        },
        imageHeight: {
            type: Number,
            default: 80
        },
        imagePrefix: {
            type: String,
            default: "images/"
        },
        imageFit: {
            type: Boolean,
            default: false
        }
    })

    const emit = defineEmits(["update"])

    const assignment = reactive(new Map())
    const selected = reactive(new Set())
    const byOption = reactive(new Map())

    function init() {
        assignment.clear()
        if (props.initial && props.initial.size > 0) {
            props.initial.forEach((v, k) => assignment.set(k, v))
        } else {
            props.items.forEach(d => assignment.set(d[props.itemId], 0))
        }

        props.options.map((_, i) => byOption.set(i, []))
        if (assignment.size > 0) {
            props.items.forEach(d => byOption.get(assignment.get(d[props.itemId])).push(d))
        }
    }

    function isVideo(d) {
        return d[props.itemImage] && d[props.itemImage].endsWith("mp4")
    }

    function allowDrop(ev) {
        ev.preventDefault();
    }

    function onDrag(_ev, id) {
        if (!selected.has(id)) {
            selected.add(id)
        }
    }
    function onClick(id) {
        if (selected.has(id)) {
            selected.delete(id)
        } else {
            selected.add(id)
        }
    }

    function onDrop(ev, target) {
        ev.preventDefault();
        if (selected.size > 0) {
            selected.forEach(id => {
                const prev = +assignment.get(id);
                if (target == prev) return;
                assignment.set(id, +target)
                const prevIdx = byOption.get(prev).findIndex(d => d[props.itemId] == id)
                if (prevIdx >= 0) {
                    const d = byOption.get(prev).splice(prevIdx, 1)[0]
                    byOption.get(target).push(d)
                }
            })
            selected.clear()
            emit("update", toRaw(assignment))
        }
    }

    onMounted(init)

    watch(() => ([props.initial, props.items, props.options]), init, { deep: true })
</script>