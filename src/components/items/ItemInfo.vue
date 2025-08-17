<template>
    <div
        :style="{
            minWidth: minW,
            width: w,
            maxHeight: maxH,
            overflowY: 'auto'
        }"
        class="pa-2 text-caption">

        <div><b>Name</b>: {{ item?.name }}</div>
        <div v-if="item?.url"><b>URL</b>: <a :href="item?.url" target="_blank">{{ item?.url }}</a></div>

        <div v-for="c in app.schema.columns" :key="'col_'+c.name" class="mt-1">
            <b>{{ capitalize(c.name) }}</b>: {{ item ? item[c.name] : '?' }}
        </div>

        <div v-if="item?.description" class="mt-1 mb-1">
            <b>Description</b>
            <p>{{ item?.description }}</p>
        </div>

    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { capitalize } from '@/use/utility';
    import { computed } from 'vue';

    const app = useApp()

    const props = defineProps({
        item: { type: Object },
        minWidth: {
            type: [String, Number],
            default: "200px"
        },
        width: {
            type: [String, Number],
            default: "auto"
        },
        maxHeight: {
            type: [String, Number],
            default: "90vh"
        }
    })

    const minW = computed(() => typeof props.minWidth === "number" ? props.minWidth+'px' : props.minWidth)
    const w = computed(() => typeof props.width === "number" ? props.width+'px' : props.width)
    const maxH = computed(() => typeof props.maxHeight === "number" ? props.maxHeight+'px' : props.maxHeight)
</script>