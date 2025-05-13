<template>
    <span
        :style="{ cursor: selectable ? 'pointer' : null, fontWeight: selected ? 'bold' : null }"
        class="hover-it"
        @click="onClick"
        @contextmenu="onRightClick"
        @pointermove="onHover"
        @pointerleave="onLeave"
        >
        {{ tagObj ? tagObj.name : '?' }}
    </span>
</template>

<script setup>
    import { pointer } from 'd3';
    import { OBJECTION_ACTIONS, useApp } from '@/store/app';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';
    import { useTooltip } from '@/store/tooltip';
    import DM from '@/use/data-manager';
    import { computed, onMounted, watch } from 'vue';
    import { useTimes } from '@/store/times';

    const app = useApp()
    const times = useTimes()
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
        },
        stopPropagation: {
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
    const selected = ref(false)

    const action = computed(() => {
        if (item.value) {
            const has = item.value.allTags.some(d => d.id === tagObj.value.id)
            return has ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD
        }
        return OBJECTION_ACTIONS.DISCUSS
    })

    function onClick(event) {
        if (props.stopPropagation) event.stopPropagation()
        if (!props.selectable) return
        if (!props.preventSelect) {
            app.toggleSelectByTag([tagObj.value.id])
        }
        emit("click", tagObj.value, event)

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
        emit("right-click", tagObj.value, event)
    }

    function onHover(event) {
        emit("hover", tagObj.value, event)
        if (props.preventHover) return
        const [mx, my] = pointer(event, document.body)
        const desc = tagObj.value.description ? "</br>"+tagObj.value.description : ""
        tt.show(`${tagObj.value.name}${desc}`, mx, my)
    }
    function onLeave(event) {
        emit("hover", null, event)
        if (props.preventHover) return
        tt.hide()
    }

    function readSelected() {
        selected.value = DM.getSelectedIds("tags").has(props.id)
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
        readSelected()
    }

    onMounted(read)

    watch(() => props.id, read)
    watch(() => props.tag, read)
    watch(() => props.itemId, readItem)
    watch(() => times.f_tags, readSelected)
</script>