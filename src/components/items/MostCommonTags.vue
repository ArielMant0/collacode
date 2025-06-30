<template>
    <div class="d-flex flex-wrap">
        <div v-for="t in tagSubset" :ref="t.id" class="text-caption mr-1 mb-1" style="width: max-content;">
            <TagText :id="t.id" prevent-context prevent-select/>
            <svg :width="width" :height="height" class="ml-2" style="display: inline;">
                <rect x="0" y="0" :height="height" :width="width" :fill="bgColor" stroke="none"></rect>
                <rect x="0" y="0" :height="height" :width="width*t.value" :fill="fillColor" stroke="none"></rect>
            </svg>
        </div>
    </div>
</template>

<script setup>
    import { useTheme } from 'vuetify';
    import TagText from '../tags/TagText.vue';
    import { computed, onMounted, watch } from 'vue';
    import { useSettings } from '@/store/settings';
    import { range } from 'd3';

    const theme = useTheme()
    const settings = useSettings()

    const props = defineProps({
        items: {
            type: Array,
        },
        tags: {
            type: Array,
        },
        limit: {
            type: Number,
            default: 5
        },
        width: {
            type: Number,
            default: 80
        },
        height: {
            type: Number,
            default: 10
        },
        valueAttr: {
            type: String,
        },
        color: {
            type: String,
        }
    })

    const tagSubset = ref([])
    const fillColor = computed(() => props.color ? props.color : theme.current.value.colors.primary)
    const bgColor = computed(() => settings.lightMode ? "#dedede" : "#343434")

    function read() {
        if (props.tags && props.valueAttr) {
            const indices = range(props.tags.length)
            indices.sort((a, b) => props.tags[b][props.valueAttr] - props.tags[a][props.valueAttr])
            tagSubset.value = indices.slice(0, props.limit).map(i => ({ id: props.tags[i].id, name: props.tags[i].name, value: props.tags[i][props.valueAttr] }))
        }
    }

    onMounted(read)
    watch(() => props.items, read)
    watch(() => props.tags, read)
    watch(() => props.limit, read)
</script>