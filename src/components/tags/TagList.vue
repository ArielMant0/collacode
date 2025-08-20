<template>
    <div class="pt-2" :style="{
        minWidth: minw,
        minHeight: minh,
        maxWidth: maxw,
        maxHeight: maxh,
        overflow: 'auto'
    }">
        <v-text-field v-model="search"
            label="Search through tags"
            variant="outlined"
            density="compact"
            @keyup.prevent.capture="onSearchKey"
            hide-details
            hide-spin-buttons
            clearable>
        </v-text-field>
        <div v-for="t in matching"
            :class="{ 'bg-primary': selIds.has(t.id) }"
            class="pa-1 cursor-pointer bordered-on-hover"
            @click="onClick(t)"
            >
            <div>
                <v-tooltip text="highlight this tag" location="top" open-delay="300">
                    <template v-slot:activator="{ props}">
                        <v-btn v-bind="props"
                            density="compact"
                            icon="mdi-image-filter-center-focus-strong"
                            variant="text"
                            class="mr-1"
                            @click.stop="onFocus(t)"
                            />
                    </template>
                </v-tooltip>
                <b>{{ t.name }}</b>
            </div>
            <div class="text-caption">{{ t.description }}</div>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { useSettings } from '@/store/settings';
    import { ref, onMounted, computed } from 'vue';

    const settings = useSettings()

    const props = defineProps({
        preventFocus: { type: Boolean, default: false },
        selected: { type: Array, default: () => ([])},
        minWidth: { type: [String, Number], default: "auto" },
        maxWidth: { type: [String, Number], default: "auto" },
        minHeight: { type: [String, Number], default: "auto" },
        maxHeight: { type: [String, Number], default: "auto" },
    })

    const emit = defineEmits(["click", "focus"])

    const selIds = computed(() => new Set(props.selected))

    const minw = computed(() => typeof props.minWidth === "number" ?
        props.minWidth+'px' :
        props.minWidth
    )
    const minh = computed(() => typeof props.minHeight === "number" ?
        props.minHeight+'px' :
        props.minHeight
    )
    const maxw = computed(() => typeof props.maxWidth === "number" ?
        props.maxWidth+'px' :
        props.maxWidth
    )
    const maxh = computed(() => typeof props.maxHeight === "number" ?
        props.maxHeight+'px' :
        props.maxHeight
    )

    const search = ref("")
    const tags = ref([])
    const matching = computed(() => {
        if (!search.value || search.value.length < 3) {
            return tags.value
        }
        const regex = new RegExp(search.value, "gi")
        return tags.value.filter(t => regex.test(t.name) || regex.test(t.description))
    })

    function onClick(tag) {
        emit("click", tag)
    }

    function onFocus(tag) {
        if (props.preventFocus) return
        settings.moveToTag(tag.id)
    }

    function onSearchKey(event) {
        if (event.code === "Escape") {
            search.value = []
        } else if (search.value && search.value.length > 2) {
            if (event.code === "Enter" && searchHits.value.length > 0) {
                setSearchTarget(searchHits.value[0])
            }
        }
    }

    function read() {
        tags.value = DM.getDataBy("tags", t => t.is_leaf === 1)
    }

    onMounted(read)
</script>