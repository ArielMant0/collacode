<template>
    <div>
        <v-text-field v-model="search"
            label="Search"
            autofocus
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="compact"
            class="mb-1"
            clearable
            hide-details
            single-line/>
        <div class="d-flex align-center flex-wrap justify-center">
            <ItemTeaser v-for="item in visible" :key="item.id"
                class="mr-1 mb-1"
                :item="item"
                @click="choose(item)"
                :width="imageWidth"
                :height="imageHeight"
                prevent-context
                prevent-open/>
        </div>
        <v-pagination v-model="page" :length="numPages" :total-visible="10"></v-pagination>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { computed, onMounted, watch } from 'vue';
    import ItemTeaser from './ItemTeaser.vue';

    const props = defineProps({
        exclude: {
            type: Array,
            required: false
        },
        imageWidth: {
            type: Number,
            default: 100
        },
        imageHeight: {
            type: Number,
            default: 50
        },
        numPerPage: {
            type: Number,
            default: 25
        }
    })

    const emit = defineEmits(["submit"])

    const search = ref("")
    const items = ref([])
    const page = ref(1)
    const numPages = computed(() => Math.ceil(matching.value.length / props.numPerPage))

    const matching = computed(() => {
        if (!search.value || search.value.length < 3) {
            return items.value
        }
        const regex = new RegExp(search.value, "gi")
        return items.value.filter(d => regex.test(d.name))
    })

    const visible = computed(() => matching.value.slice((page.value-1)*props.numPerPage, page.value*props.numPerPage))

    function read() {
        const ex = new Set(props.exclude ? props.exclude : [])
        items.value = ex.size > 0 ?
            DM.getDataBy("items", d => !ex.has(d.id)) :
            DM.getData("items", false)
    }

    function choose(item) {
        emit("submit", item)
    }

    onMounted(read)

    watch(numPages, function() {
        if (page.value > numPages.value) {
            page.value = numPages.value
        }
    })
</script>