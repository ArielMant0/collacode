<template>
    <div class="d-flex flex-wrap">
        <div v-for="t in tagSubset" :ref="t.id+'_'+t.value" class="d-flex align-center text-caption" style="width: max-content;">
            <svg :width="width" :height="height" class="mr-2" style="display: inline;">
                <rect x="0" y="0" :height="height" :width="width" :fill="bgColor" stroke="none"></rect>
                <rect x="0" y="0" :height="height" :width="width*t.value" :fill="fillColor" stroke="none"></rect>
            </svg>
            <div class="text-dots" :style="{ maxWidth: (width*2)+'px' }">
                <TagText :id="t.id" prevent-context :selectable="false"/>
            </div>
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
        tags: {
            type: Array,
            required: true
        },
        valueAttr: {
            type: String,
            required: true
        },
        time: {
            type: Number,
            default: 0
        },
        limit: {
            type: Number,
            default: 5
        },
        width: {
            type: Number,
            default: 60
        },
        height: {
            type: Number,
            default: 10
        },
        color: {
            type: String,
        },
    })

    const tagSubset = ref([])
    const fillColor = computed(() => props.color ? props.color : theme.current.value.colors.primary)
    const bgColor = computed(() => settings.lightMode ? "#dedede" : "#343434")

    function read() {
        const indices = range(props.tags.length)
        indices.sort((a, b) => props.tags[b][props.valueAttr] - props.tags[a][props.valueAttr])
        tagSubset.value = indices.slice(0, props.limit).map(i => ({ id: props.tags[i].id, name: props.tags[i].name, value: props.tags[i][props.valueAttr] }))
    }

    onMounted(read)

    watch(() => props.time, read)

</script>