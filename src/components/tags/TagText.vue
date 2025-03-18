<template>
    <span
        :style="{ cursor: selectable ? 'pointer' : null }"
        class="hover-it"
        @click="onClick"
        @contextmenu="onRightClick"
        @pointermove="onHover"
        @pointerleave="onLeave"
        >
        {{ tagObj.name }}
    </span>
</template>

<script setup>
    import { pointer } from 'd3';
    import { OBJECTION_ACTIONS, useApp } from '@/store/app';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useTooltip } from '@/store/tooltip';
    import DM from '@/use/data-manager';
    import { computed, onMounted, watch } from 'vue';

    const app = useApp()
    const tt = useTooltip()
    const settings = useSettings()

    const props = defineProps({
        id: {
            type: Number,
            required: false
        },
        tag: {
            type: Object,
            required: false
        },
        itemId: {
            type: Number,
            required: false
        },
        selectable: {
            type: Boolean,
            default: true
        },
        preventSelect: {
            type: Boolean,
            default: false
        },
        preventContext: {
            type: Boolean,
            default: false
        },
        preventHover: {
            type: Boolean,
            default: false
        }
    })

    const emit = defineEmits(["click", "right-click", "hover"])

    const tagObj = ref({
        id: -1,
        name: "?"
    })

    const item = ref(null)
    const action = computed(() => {
        if (item.value) {
            const has = item.value.allTags.some(d => d.id === tagObj.value.id)
            return has ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD
        }
        return OBJECTION_ACTIONS.DISCUSS
    })

    function onClick() {
        if (!props.selectable) return
        if (!props.preventSelect) {
            app.toggleSelectByTag([tagObj.value.id])
        }
        emit("click", tagObj.value)

    }

    function onRightClick(event) {
        event.preventDefault()
        if (!props.selectable) return
        if (!props.preventContext) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "tag",
                tagObj.value.id,
                mx, my,
                tagObj.value.name,
                item.value ? { item: item.value.id, tag: tagObj.value.id, action: action } : null,
                item.value ? CTXT_OPTIONS.items_tagged : CTXT_OPTIONS.tag
            )
        }
        emit("right-click", tagObj.value)
    }

    function onHover(event) {
        if (props.preventHover) return
        const [mx, my] = pointer(event, document.body)
        const desc = tagObj.value.description ? "</br>"+tagObj.value.description : ""
        tt.show(`${tagObj.value.name}${desc}`, mx, my)
    }
    function onLeave() {
        if (props.preventHover) return
        tt.hide()
    }

    function readItem() {
        item.value = props.itemId ? DM.getDataItem("items", props.itemId) : null
    }
    function read() {
        if (props.id) {
            tagObj.value = DM.getDataItem("tags", props.id)
        } else {
            tagObj.value = props.tag;
        }
        readItem()
    }

    onMounted(read)

    watch(() => props.id, read)
    watch(() => props.tag, read)
    watch(() => props.itemId, readItem)
</script>