<template>
    <span :class="{ 'cursor-pointer': selectable }">
        <video v-if="isVideoFile"
            class="a-0"
            :src="mediaPath(mediaType, path)"
            :autoplay="autoplay"
            :controls="controls"
            :playsinline="playsinline"
            :height="height"
            :style="{ maxWidth: maxW, maxHeight: maxH }"
            >
        </video>

        <v-img v-else
            :src="path? mediaPath(mediaType, path) : imgUrlS"
            :lazy-src="imgUrlS"
            v-ripple.center
            :cover="!imageFit"
            :height="height"
            :style="{ maxWidth: maxW, maxHeight: maxH }"
            >
        </v-img>
    </span>
</template>

<script setup>
    import imgUrlS from '@/assets/__placeholder__s.png'
    import { isVideo, mediaPath } from '@/use/utility';
    import { computed } from 'vue';

    const props = defineProps({
        path: {
            type: String,
            required: true
        },
        mediaType: {
            type: String,
            required: true
        },
        height:  {
            type: Number,
            default: 200
        },
        maxWidth:  {
            type: [Number, String],
            default: "50vw"
        },
        maxHeight:  {
            type: [Number, String],
            default: "200px"
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
        imageFit: {
            type: Boolean,
            default: true
        }
    })

    const isVideoFile = computed(() => isVideo(props.path))

    const maxW = computed(() => props.maxWidth + (typeof props.maxWidth === "number" ? "px" : ""))
    const maxH = computed(() => props.maxHeight + (typeof props.maxHeight === "number" ? "px" : ""))

</script>