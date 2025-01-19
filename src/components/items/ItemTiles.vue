<template>
    <div class="d-flex flex-wrap">
        <v-img v-for="d in data.items"
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
    import { useTimes } from '@/store/times';

    import imgUrlS from '@/assets/__placeholder__s.png'

    const props = defineProps({
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

    const times = useTimes()

    const data = reactive({ items: [] })

    function readData() {
        data.items = DM.getData("items", true);
    }

    onMounted(readData)

    watch(() => Math.max(times.items, times.f_items), readData)
</script>