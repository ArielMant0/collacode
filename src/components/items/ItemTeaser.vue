<template>
    <div
        class="container"
        :style="{ width: width+'px', fontSize: fontSize+'px', cursor: preventClick ? 'default' : 'pointer' }">
        <div v-if="showName" class="text-caption text-dots" :style="{ maxWidth: width+'px' }">{{ itemObj.name }}</div>
        <v-sheet
            style="position: relative;"
            :style="{ height: height+'px', border: border, padding: padding }">
            <v-img
                :cover="!contain"
                :src="itemObj.teaser ? 'teaser/'+itemObj.teaser : imgUrlS"
                :lazy-src="imgUrlS"
                :width="width"
                :height="height"/>
            <div class="overlay"
                style="overflow: hidden;"
                @click="onClick"
                @contextmenu="onRightClick"
                @pointermove="onHover"
                @pointerleave="tt.hide()">
                <div class="text">{{ itemObj.name }}</div>
            </div>
        </v-sheet>
    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { useApp } from '@/store/app';
    import { useTooltip } from '@/store/tooltip';
    import { computed, onBeforeUnmount, onMounted } from 'vue';
    import DM from '@/use/data-manager';
    import { CTXT_OPTIONS, useSettings } from '@/store/settings';

    const app = useApp()
    const tt = useTooltip()
    const settings = useSettings()

    const props = defineProps({
        id: { type: Number },
        item: { type: Object },
        width: {
            type: Number,
            default: 160
        },
        height: {
            type: Number,
            default: 80
        },
        contain: {
            type: Boolean,
            default: false
        },
        borderColor: {
            type: String,
        },
        borderStyle: {
            type: String,
            default: "solid"
        },
        borderSize: {
            type: Number,
            default: 1
        },
        zoomOnHover: {
            type: Boolean,
            default: false
        },
        showName: {
            type: Boolean,
            default: false
        },
        preventClick: {
            type: Boolean,
            default: false
        },
        preventOpen: {
            type: Boolean,
            default: false
        },
        preventContext: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["click", "right-click", "hover"])

    const itemObj = reactive({
        id: null,
        name: "",
        teaser: "",
    })

    const fontSize = computed(() => {
        if (props.height < 50) {
            return itemObj.name.length < 20 ? 12 : 10
        } else if (props.height < 25) {
            return itemObj.name.length < 20 ? 8 : 6
        }
        return itemObj.name.length < 20 ? 14 : 12
    })

    const border = computed(() => {
        if (!props.borderColor) return ""
        return `${props.borderSize}px ${props.borderStyle} ${props.borderColor}`
    })
    const padding = computed(() => {
        if (border.value.length === 0) {
            return "0px"
        }
        return Math.max(1, Math.min(10, Math.round(Math.min(props.width, props.height) * 0.01))) + "px"
    })

    onBeforeUnmount(() => tt.hide())

    function onClick() {
        if (props.preventClick) return
        if (!props.preventOpen) app.setShowItem(itemObj.id)
        emit("click")
    }
    function onRightClick(event) {
        event.preventDefault()
        if (props.preventClick) return
        if (!props.preventContext) {
            const [mx, my] = pointer(event, document.body)
            settings.setRightClick(
                "item",
                itemObj.id,
                mx, my,
                itemObj.name,
                null,
                CTXT_OPTIONS.items
            )

        }
        emit("right-click")
    }
    function onHover(event) {
        if (!itemObj.teaser || !props.zoomOnHover) return
        const [mx, my] = pointer(event, document.body)
        tt.show(
            `<img src="teaser/${itemObj.teaser}" style="max-height: 250px; object-fit: contain;"/>`,
            mx, my
        )
        emit("hover")
    }

    function readItem() {
        if (props.id) {
            const tmp = DM.getDataItem("items", props.id)
            itemObj.name = tmp.name ? tmp.name : ""
            itemObj.teaser = tmp.teaser ? tmp.teaser : ""
            itemObj.id = props.id
        } else if (props.item) {
            itemObj.name = props.item.name
            itemObj.teaser = props.item.teaser
            itemObj.id = props.item.id
        }
    }

    onMounted(readItem)

    watch(() => ([props.id, props.item]), readItem, { deep: true })
</script>

<style scoped>
.container {
    height: max-content;
}
.overlay {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    height: 100%;
    width: 100%;
    opacity: 0;
    transition: .5s ease;
    background-color: black;
}
.container:hover .overlay {
    opacity: 0.8;
}

.text {
    color: white;
    position: absolute;
    text-align: center;
    line-height: 1em;
    width: 100%;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    -ms-transform: translate(-50%, -50%);
}
</style>