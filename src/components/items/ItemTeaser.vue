<template>
    <div
        class="container"
        :style="{ width: width+'px', height: height+'px', fontSize: fontSize+'px', cursor: preventClick ? 'default' : 'pointer' }">
        <v-img v-if="item.teaser"
            :cover="!contain"
            :src="item.teaser ? 'teaser/'+item.teaser : imgUrlS"
            :lazy-src="imgUrlS"
            :width="width"
            :height="height"/>
        <div v-else :style="{ width: width+'px', height: height+'px' }">
            {{ item.name }}
        </div>
        <div class="overlay"
            style="overflow: hidden;"
            @click="onClick"
            @pointermove="onHover"
            @pointerleave="tt.hide()">
            <div class="text">{{ item.name }}</div>
        </div>
    </div>
</template>

<script setup>
    import { pointer } from 'd3';
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { useApp } from '@/store/app';
    import { useTooltip } from '@/store/tooltip';
    import { computed, onBeforeUnmount } from 'vue';

    const app = useApp()
    const tt = useTooltip()

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
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
        zoomOnHover: {
            type: Boolean,
            default: false
        },
        preventClick: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["click", "hover"])

    const fontSize = computed(() => {
        if (props.height < 50) {
            return props.item.name.length < 20 ? 12 : 10
        } else if (props.height < 25) {
            return props.item.name.length < 20 ? 8 : 6
        }
        return props.item.name.length < 20 ? 14 : 12
    })

    onBeforeUnmount(() => tt.hide())

    function onClick() {
        if (props.preventClick) return
        app.setShowItem(props.item.id)
        emit("click")
    }
    function onHover(event) {
        if (!props.item.teaser || !props.zoomOnHover) return
        const [mx, my] = pointer(event, document.body)
        tt.show(
            `<img src="teaser/${props.item.teaser}" style="max-height: 250px; object-fit: contain;"/>`,
            mx, my
        )
        emit("hover")
    }
</script>

<style scoped>
.container {
    position: relative;
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
    opacity: 0.75;
}

.text {
    color: white;
    position: absolute;
    text-align: center;
    line-height: 1em;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    -ms-transform: translate(-50%, -50%);
}
</style>