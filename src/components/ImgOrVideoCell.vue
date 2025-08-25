<template>
    <span :class="{ 'cursor-pointer': selectable }">
        <video v-if="isVideoFile"
            class="a-0"
            :src="mediaPath(mediaType, path)"
            :autoplay="autoplay"
            :controls="controls"
            :playsinline="playsinline"
            @mousemove="onHoverShow"
            @mouseleave="onHoverHide"
            :width="size"
            :height="size">
        </video>

        <v-img v-else
            :src="path? mediaPath(mediaType, path) : imgUrlS"
            v-ripple.center
            :cover="!imageFit"
            @mousemove="onHoverShow"
            @mouseleave="onHoverHide"
            :width="size"
            :height="size">
        </v-img>
    </span>
</template>

<script setup>
    import { pointer } from 'd3';
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { useTooltip } from '@/store/tooltip';
    import { isVideo, mediaPath } from '@/use/utility';
    import { computed } from 'vue';

    const tt = useTooltip()

    const props = defineProps({
        path: {
            type: String,
            required: true
        },
        mediaType: {
            type: String,
            required: true
        },
        mediaSize:  {
            type: Number,
            default: 100
        },
        imageFit: {
            type: Boolean,
            default: false
        },
        autoplay: {
            type: Boolean,
            default: false
        },
        controls: {
            type: Boolean,
            default: false
        },
        playsinline: {
            type: Boolean,
            default: true
        },
        selectable: {
            type: Boolean,
            default: false
        },
        zoomOnHover: {
            type: Boolean,
            default: false
        }
    })

    const isVideoFile = computed(() => isVideo(props.path))
    const size = computed(() => isVideoFile.value ? props.mediaSize-7 : props.mediaSize)

    function onHoverShow(event) {
        const [mx, my] = pointer(event, document.body)
        if (isVideoFile.value) {
            tt.showVideo(mediaPath(props.mediaType, props.path), mx, my)
        } else {
            tt.showImage(mediaPath(props.mediaType, props.path), mx, my)
        }
    }

    function onHoverHide() {
        tt.hide()
    }
</script>