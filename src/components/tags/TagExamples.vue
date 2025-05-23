<template>
    <v-card v-if="model"
        class="my-window"
        elevation="8"
        rounded
        min-height="95vh"
        :style="{ left: wL, right: wR }"
        density="compact">

        <v-card-title>
            <v-btn density="compact" size="small" variant="plain" @click="goLeft" :disabled="wL !== 'auto'" icon="mdi-arrow-left"/>
            <v-btn density="compact" size="small" variant="plain" @click="goRight" :disabled="wR !== 'auto'" icon="mdi-arrow-right"/>
            Examples for tag "{{ name }}"
            <v-btn style="float: right;" icon="mdi-close" color="error" variant="plain" density="compact" @click="close"/>
        </v-card-title>

        <v-card-text class="pt-2">

            <div class="d-flex align-center justify-center mb-2">
                <v-checkbox-btn
                    v-model="showAllUsers"
                    color="primary"
                    density="compact"
                    inline
                    true-icon="mdi-tag"
                    false-icon="mdi-tag-off"
                    :disabled="app.static"/>

                <span class="ml-1 text-caption">using {{ showAllUsers ? 'tags for all coders' : 'only your tags' }}</span>
            </div>

            <div style="max-height: 85vh; overflow-y: auto;" class="d-flex flex-wrap">
                <div v-for="d in items" :key="'example_'+d.id" class="text-caption mr-2">
                    <div class="text-dots" :style="{ maxWidth: imgWidth+'px' }" :title="d.name">{{ d.name }}</div>
                    <div class="d-flex">
                        <ItemTeaser :item="d" :width="imgWidth" :height="imgHeight"/>

                            <div class="ml-1 d-flex flex-wrap flex-column" :style="{ maxHeight: imgHeight+'px' }">
                                <v-icon v-for="(e, idx) in d.evidence"
                                    icon="mdi-circle"
                                    size="xx-small"
                                    class="mb-1"
                                    @pointerenter="event => hoverEvidence(e, event)"
                                    @pointerleave="hoverEvidence(null)"
                                    @click="app.setShowEvidence(
                                        e.id,
                                        d.evidence.map(dd => dd.id),
                                        idx,
                                    )"
                                    :color="app.getUserColor(e.created_by)"/>
                            </div>
                    </div>
                </div>

            </div>
        </v-card-text>
    </v-card>
</template>

<script setup>
    import { pointer } from 'd3';
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import { onMounted, watch } from 'vue';
    import { useTooltip } from '@/store/tooltip';
    import { useSettings } from '@/store/settings';
    import Cookies from 'js-cookie';

    const app = useApp()
    const settings = useSettings()
    const times = useTimes()
    const tt = useTooltip()

    const model = defineModel()
    const props = defineProps({
        id: {
            type: Number,
        },
        imgWidth: {
            type: Number,
            default: 100
        },
        imgHeight: {
            type: Number,
            default: 50
        },
    })
    const emit = defineEmits(["close"])

    const showAllUsers = ref(app.showAllUsers)
    const name = ref("")
    const items = ref([])

    const wL = ref("80px")
    const wR = ref("auto")

    function goLeft() {
        wL.value = "80px"
        wR.value = "auto"
        settings.setPanelSide("left")
    }
    function goRight() {
        wR.value = "20px"
        wL.value = "auto"
        settings.setPanelSide("right")
    }
    function close() {
        tt.hideEvidence()
        emit("close")
    }

    function hoverEvidence(e, event) {
        if (e) {
            const [mx, my] = pointer(event, document.body)
            tt.showEvidence(e.id, mx, my)
        } else {
            tt.hideEvidence()
        }
    }

    function hasTag(d) {
        if (!props.id) return false
        return showAllUsers.value ?
            d.allTags.some(t => {
                const p = DM.getDerivedItem("tags_path", t.id)
                return t.id === props.id || (p && p.path.includes(props.id))
            }) :
            d.tags.some(dt => {
                const p = DM.getDerivedItem("tags_path", dt.tag_id)
                return dt.created_by === app.activeUserId && (dt.tag_id === props.id || (p && p.path.includes(props.id)))
            })
    }
    function getTagEvidence(d) {
        if (!props.id) return []
        return d.evidence.filter(e => e.tag_id === props.id && (showAllUsers.value || e.created_by === app.activeUserId))
    }

    function readExamples() {
        model.value = props.id !== undefined && props.id !== null
        if (!props.id) {
            name.value = ""
            items.value = []
            return
        }

        const side = Cookies.get("panel-side")
        if (side === "left") {
            goLeft()
        } else {
            goRight()
        }

        name.value = DM.getDataItem("tags_name", props.id)
        const data = showAllUsers.value ?
            DM.getDataBy("items", d => d.numTags > 0) :
            DM.getDataBy("items", d => d.coders.includes(app.activeUserId))

        const array = []
        data.forEach(d => {
            const match1 = hasTag(d)
            if (match1) {
                array.push({
                    id: d.id,
                    name: d.name,
                    teaser: d.teaser,
                    evidence: getTagEvidence(d)
                })
            }
        })
        array.sort((a, b) => b.evidence.length - a.evidence.length)

        items.value = array
    }

    onMounted(readExamples)

    watch(() => props.id, readExamples)
    watch(() => Math.max(times.tagging, times.datasets, times.evidence), readExamples)
    watch(showAllUsers, readExamples)

</script>

<style scoped>
.my-window {
    position: fixed;
    top: 35px;
    user-select: none;
    width: 32%;
    min-width: 350px;
    height: 95vh;
    z-index: 3;
}
</style>