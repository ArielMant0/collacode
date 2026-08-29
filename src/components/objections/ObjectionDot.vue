<template>
    <ObjectionIcon
        v-if="obj"
        :action="obj.action"
        class="cursor-pointer"
        @pointerenter="enter"
        @pointerleave="leave"
        @click="click"
        @contextmenu.prevent="rightClick"
        :size="size"
        />
</template>

<script setup>
    import { pointer } from 'd3';
    import { useTooltip } from '@/store/tooltip';
    import DM from '@/use/data-manager';
    import { onMounted, watch } from 'vue';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useApp } from '@/store/app';
    import ObjectionIcon from './ObjectionIcon.vue';

    const app = useApp()
    const settings = useSettings()
    const tt = useTooltip()

    const props = defineProps({
        id: { type: Number, required: false },
        objection: { type: Object, required: false },
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
        tt.showObjection(obj.value.id, mx, my)
    }
    function leave(event) {
        emit("hover", null, event)
        if (props.hideTooltip) return
        tt.hideObjection()
    }
    function click(event) {
        emit("click", obj.value, event)
        if (props.preventOpen) return
        app.setShowObjection(obj.value.id)
    }
    function rightClick(event) {
        emit("right-click", obj.value, event)
        if (props.preventContext) return
        const [mx, my] = pointer(event, document.body)
        settings.setRightClick(
            "objection",
            obj.value.id,
            mx, my,
            null,
            {
                item: obj.value.item_id,
                tag: obj.value.tag_id
            },
            CTXT_OPTIONS.objections
        )
    }

    function read() {
        if (props.objection) {
            obj.value = props.objection
        } else if (props.id) {
            obj.value = DM.getDataItem("objections", props.id)
        } else {
            obj.value = null
        }
    }

    onMounted(read)

    watch(() => props.id, read)
    watch(() => props.objection, read)
</script>