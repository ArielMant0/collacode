<template>
    <div class="d-flex flex-wrap">
        <v-img v-for="d in data.games"
            :src="'teaser/'+d.teaser"
            :lazy-src="imgUrlS"
            class="ma-1"
            cover
            :width="width"
            :height="height"/>
    </div>
</template>

<script setup>
    import { reactive, onMounted, watch } from 'vue';
    import DM from '@/use/data-manager'
    import imgUrlS from '@/assets/__placeholder__s.png'

    const props = defineProps({
        time: {
            type: Number,
            required: true
        },
        selected: {
            type: Object,
            required: false
        },
        highlightClicked: {
            type: Boolean,
            default: false
        },
        width: {
            type: Number,
            default: 150
        },
        height: {
            type: Number,
            default: 75
        },
    });

    const data = reactive({ games: [] })

    function readData() {
        data.games = DM.getData("games", true);
    }

    onMounted(readData)

    watch(() => props.time, readData)
</script>