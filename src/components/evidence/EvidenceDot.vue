<template>
    <v-icon v-if="obj"
        :color="app.getUserColor(obj.created_by)"
        class="cursor-pointer"
        @pointerenter="enter"
        @pointerleave="leave"
        @click="click"
        @contextmenu.prevent="rightClick"
        :size="size">
        mdi-circle
    </v-icon>
</template>

<script setup>
    import { pointer } from 'd3';
    import { useTooltip } from '@/store/tooltip';
    import DM from '@/use/data-manager';
    import { onMounted, watch } from 'vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useApp } from '@/store/app';

    const app = useApp()
    const settings = useSettings()
    const tt = useTooltip()

    const props = defineProps({
        id: { type: Number, required: false },
        evidence: { type: Object, required: false },
        list: { type: Array, required: false },
        index: { type: Number, required: false },
        size: { type: String, default: "xx-small" },
        hideTooltip: { type: Boolean, default: false },
        preventOpen: { type: Boolean, default: false },
        preventContext: { type: Boolean, default: false },
    })

    const emit = defineEmits(["hover", "click", "right-click"])
    const obj = ref(null)

    function enter(event) {
        emit("hover", obj.value, event)
        if (props.hideTooltip) return
        const [mx, my] = pointer(event, document.body)
        tt.showEvidence(obj.value.id, mx, my)
    }
    function leave(event) {
        emit("hover", null, event)
        if (props.hideTooltip) return
        tt.hideEvidence()
    }
    function click(event) {
        emit("click", obj.value, event)
        if (props.preventOpen) return
        if (props.list !== undefined && props.index !== undefined) {
            app.setShowEvidence(obj.value.id, props.list, props.index)
        } else {
            app.setShowEvidence(obj.value.id)
        }
    }
    function rightClick(event) {
        emit("right-click", obj.value, event)
        if (props.preventContext) return
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "evidence",
            obj.value.id,
            mx, my,
            null,
            {
                item: obj.value.item_id,
                tag: obj.value.tag_id
            },
            CTXT_OPTIONS.evidence
        )
    }

    function read() {
        if (props.evidence) {
            obj.value = props.evidence
        } else if (props.id) {
            obj.value = DM.getDataItem("evidence", props.id)
        } else {
            obj.value = null
        }
    }

    onMounted(read)

    watch(() => props.id, read)
    watch(() => props.evidence, read)
</script>