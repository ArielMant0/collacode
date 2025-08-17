<template>
    <SidePanel v-model="model" :title="'Examples for tag '+name" @close="close" width="35vw">
        <template #text>
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
                            <EvidenceDot v-for="(e, idx) in d.evidence"
                                class="mb-1"
                                :evidence="e"
                                :index="idx"
                                :list="d.evidence.map(dd => dd.id)"/>
                        </div>
                    </div>
                </div>

            </div>
        </template>
    </SidePanel>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import { onMounted, watch } from 'vue';
    import { useTooltip } from '@/store/tooltip';
    import SidePanel from '../dialogs/SidePanel.vue';
    import EvidenceDot from '../evidence/EvidenceDot.vue';

    const app = useApp()
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
        zIndex: {
            type: Number,
            default: 2999,
        }
    })
    const emit = defineEmits(["close"])

    const showAllUsers = ref(app.showAllUsers)
    const name = ref("")
    const items = ref([])

    function close() {
        tt.hideAll()
        emit("close")
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
    watch(() => Math.max(times.tagging, times.datatags, times.evidence), readExamples)
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