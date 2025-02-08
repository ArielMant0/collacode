<template>
    <v-dialog :model-value="model"
        class="my-window"
        elevation="8"
        opacity="0"
        :style="{ left: wL, right: wR }"
        @after-leave="checkClose"
        density="compact">

        <v-card density="compact">
            <v-card-title>
                <v-btn density="compact" size="small" variant="plain" @click="goLeft" :disabled="wL !== 'auto'" icon="mdi-arrow-left"/>
                <v-btn density="compact" size="small" variant="plain" @click="goRight" :disabled="wR !== 'auto'" icon="mdi-arrow-right"/>
                Examples for tag "{{ name }}"
                <v-btn style="float: right;" icon="mdi-close" color="error" variant="plain" density="compact" @click="close"/>
            </v-card-title>
            <v-card-text class="pt-2">

                <div class="d-flex align-center mb-2">
                    <v-checkbox-btn
                        :model-value="showAllUsers"
                        color="primary"
                        density="compact"
                        inline
                        true-icon="mdi-tag"
                        false-icon="mdi-tag-off"
                        :disabled="app.static"
                        @click="app.toggleUserVisibility"/>

                    <span class="ml-1 text-caption">using {{ showAllUsers ? 'tags for all coders' : 'only your tags' }}</span>
                </div>

                <div style="max-height: 80vh; overflow-y: auto;" class="d-flex flex-wrap">
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
    </v-dialog>
    <ToolTip :x="hoverE.x" :y="hoverE.y" :data="hoverE.data">
        <template v-slot:default>
            <EvidenceCell :item="hoverE.data" :height="200" image-fit show-desc/>
        </template>
    </ToolTip>
</template>

<script setup>
    import { pointer } from 'd3';
    import { useApp } from '@/store/app';
    import DM from '@/use/data-manager';
    import ToolTip from '../ToolTip.vue';
    import EvidenceCell from '../evidence/EvidenceCell.vue';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import { storeToRefs } from 'pinia';
    import { onMounted, reactive, watch } from 'vue';

    const app = useApp()
    const { showAllUsers } = storeToRefs(app)

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

    const name = ref("")
    const items = ref([])
    const hoverE = reactive({
        x: 0,
        y: 0,
        data: null
    })

    const wL = ref("25px")
    const wR = ref("auto")

    function goLeft() {
        wL.value = "25px"
        wR.value = "auto"
    }
    function goRight() {
        wR.value = "25px"
        wL.value = "auto"
    }
    function close() {
        hoverE.data = null
        emit("close")
    }

    function hoverEvidence(e, event) {
        if (e) {
            const [mx, my] = pointer(event, document.body)
            hoverE.x = mx + 15;
            hoverE.y = my
            hoverE.data = e
        } else {
            hoverE.data = null
        }
    }

    function hasTag(d) {
        if (!props.id) return false
        return showAllUsers.value ?
            d.allTags.some(t => t.id === props.id) :
            d.tags.some(dt => dt.tag_id === props.id && dt.created_by === app.activeUserId)
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

    function checkClose() {
        if (props.id) {
            emit("close")
        }
    }

    onMounted(readExamples)

    watch(() => props.id, readExamples)
    watch(showAllUsers, readExamples)

</script>

<style scoped>
.my-window {
    position: fixed;
    user-select: none;
    top: 25px;
    width: 32%;
    min-width: 350px;
    height: 95vh;
}
</style>