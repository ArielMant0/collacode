<template>
    <div v-if="item.id > 0">
        <div class="d-flex align-center mb-1">
            <ItemTeaser :id="id" :width="teaserWidth" :height="teaserHeight" :border-color="teaserBorder" :border-size="2"/>
            <span class="ml-2">{{ item.name }}</span>
        </div>

        <BarCode v-if="barData.length > 0"
            :item-id="item.id"
            :data="barData"
            :domain="barDomain"
            hide-highlight
            selectable
            categorical
            @right-click="openTagContext"
            id-attr="0"
            name-attr="1"
            desc-attr="2"
            value-attr="3"
            abs-value-attr="3"
            hide-value
            selected-color="red"
            :color-domain="[1, 2]"
            :color-scale="[
                settings.lightMode ? 'black' : 'white',
                settings.lightMode ? '#0ad39f' : '#078766',
            ]"
            :no-value-color="settings.lightMode ? '#f2f2f2' : '#333333'"
            :width="barCodeNodeSize"
            :height="barCodeHeight"/>

        <div v-if="showEvidence" class="mt-1 d-flex flex-wrap">
            <EvidenceCell v-for="(e, idx) in evidence" :key="'ev_'+e.id"
                @select="app.setShowEvidence(e.id, evidenceIds, idx)"
                :width="evidenceSize"
                :height="evidenceSize"
                :item="e"/>
        </div>
    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import DM from '@/use/data-manager';
    import ItemTeaser from './ItemTeaser.vue';
    import BarCode from '../vis/BarCode.vue';
    import EvidenceCell from '../evidence/EvidenceCell.vue';
    import { storeToRefs } from 'pinia';
    import { OBJECTION_ACTIONS, useApp } from '@/store/app';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { ref, onMounted, watch, computed } from 'vue';

    const app = useApp()
    const settings = useSettings()

    const { showAllUsers } = storeToRefs(app)
    const { barCodeNodeSize } = storeToRefs(settings)

    const props = defineProps({
        id: {
            type: Number,
            required: true
        },
        tagId: {
            type: [Number, null],
            default: null
        },
        showEvidence: {
            type: Boolean,
            default: false
        },
        showAllUsers: {
            type: Boolean,
            default: false
        },
        barCodeHeight: {
            type: Number,
            default: 15
        },
        teaserWidth: {
            type: Number,
            default: 160
        },
        teaserHeight: {
            type: Number,
            default: 80
        },
        teaserBorder: {
            type: String,
        },
        evidenceSize: {
            type: Number,
            default: 120
        },
    })

    const item = ref({
        id: -1,
        name: "?",
        evidence: [],
        tags: [],
        allTags: []
    })

    const barData = ref([])
    const barDomain = ref([])

    const evidence = computed(() => {
        if (!props.showEvidence) {
            return []
        }

        if (props.tagId) {
            return item.value.evidence.filter(d => d.tag_id === props.tagId)
        }
        return item.value.evidence
    })
    const evidenceIds = computed(() => evidence.value.map(d => d.id))



    function openTagContext(tag, event, has) {
        const [x, y] = pointer(event, document.body)
        const action = has ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD
        settings.setRightClick(
            "tag", tag[0],
            x, y,
            tag[1],
            { action: action },
            CTXT_OPTIONS.items_tagged
        )
    }

    function readBarData() {
        if (!item.value) {
            barData.value = []
            return
        }

        let tmp;
        if (props.showAllUsers || showAllUsers.value) {
            tmp = item.value.allTags
        } else {
            tmp = item.value.tags
                .filter(d => d.created_by === app.activeUserId)
                .map(d => item.value.allTags.find(dd => dd.id === d.tag_id))
        }

        barData.value = tmp.map(d => ([
            d.id,
            d.name,
            DM.getDataItem("tags_desc", d.id),
            props.tagId && d.id === props.tagId ? 2 : 1
        ]))
    }
    function updateBarData() {
        barData.value.forEach(d => {
            if (props.tagId && d[0] === props.tagId) {
                d[3] = 2
            }
        })
    }

    function read() {
        item.value = DM.getDataItem("items", props.id)
        barDomain.value = DM.getDataBy("tags_tree", d => d.is_leaf === 1).map(d => d.id)
        readBarData()
    }

    onMounted(read)

    watch(() => props.id, read)
    watch(showAllUsers, readBarData)
    watch(() => props.tagId, updateBarData)
</script>