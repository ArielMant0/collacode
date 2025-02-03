<template>
    <div>
        <v-text-field
            v-model="name"
            density="compact"
            label="Name"
            class="mb-1"
            hide-details
            hide-spin-buttons/>
        <v-select
            v-model="parent"
            :items="cats"
            label="Parent Category"
            item-title="name"
            item-value="id"
            density="compact"
            hide-details
            hide-spin-buttons
            class="mb-1"
            />
        <v-textarea
            v-model="desc"
            density="compact"
            label="Description"
            hide-details
            hide-spin-buttons/>

        <div v-if="allowEdit" class="mt-2 d-flex justify-space-between">
            <v-btn append-icon="mdi-delete"
                class="mr-1"
                variant="tonal"
                :disabled="!hasChanges"
                :color="hasChanges? 'error' : 'default'"
                @click="discard"
                >
                discard
            </v-btn>
            <v-btn v-if="existing"
                append-icon="mdi-close"
                class="ml-1 mr-1"
                variant="tonal"
                color="error"
                @click="remove"
                >
                delete
            </v-btn>
            <v-btn append-icon="mdi-sync"
                class="ml-1"
                variant="tonal"
                :disabled="!hasChanges"
                :color="hasChanges? 'secondary' : 'default'"
                @click="update"
                >
                {{ props.item.id ? "update": "create" }}
            </v-btn>
        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import { useToast } from 'vue-toastification';
    import { createExtCategory, deleteExtCategories, updateExtCategory } from '@/use/utility';
    import { ref, computed, onMounted, watch } from 'vue';
    import DM from '@/use/data-manager';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        allowEdit: {
            type: Boolean,
            default: false
        },
    })

    const name = ref("")
    const desc = ref("")
    const parent = ref(null)
    const existing = computed(() => props.item.id !== null && props.item.id !== undefined)

    const cats = ref([])

    const emit = defineEmits(["update", "cancel"])

    const hasChanges = computed(() => {
        return props.item.name !== name.value ||
            (props.item.parent !== null && props.item.parent >= 0 && (parent.value === null || props.item.parent !== parent.value)) ||
            ((props.item.parent < 0 || props.item.parent === null) && parent.value !== null && parent.value > 0) ||
            props.item.description !== desc.value
    })

    async function update() {

        if (!name.value) { return toast.error("missing name") }
        if (!desc.value) { return toast.error("missing description") }

        try {
            if (props.item.id) {
                props.item.name = name.value;
                props.item.description = desc.value;
                props.item.parent = parent.value && parent.value >= 0 ? parent.value : null;
                await updateExtCategory(props.item)
                toast.success("updated externalization category")
            } else {
                await createExtCategory(
                    app.ds,
                    app.currentCode,
                    {
                        name: name.value,
                        description: desc.value,
                        parent: parent.value,
                        created: Date.now(),
                        created_by: app.activeUserId
                    }
                )
                toast.success("created new meta category")
            }
            emit("update")
            times.needsReload("meta_categories")
        } catch {
            toast.error("error creating new category")
        }
    }

    function discard() {
        if (hasChanges.value) {
            read();
        }
    }
    async function remove() {
        if (props.allowEdit && existing.value) {
            try {
                await deleteExtCategories([props.item.id])
                toast.success("deleted category " + props.item.name)
                times.needsReload("meta_categories")
                emit("cancel")
            } catch (e) {
                console.error(e.toString())
                toast.error("error deleting category " + props.item.name)
            }
        }
    }

    function read() {
        name.value = props.item.name
        desc.value = props.item.description
        parent.value = props.item.parent && props.item.parent >= 0 ? props.item.parent : null
    }

    onMounted(function() {
        cats.value = [{ id: null, name: "<none>" }].concat(DM.getData("meta_categories"))
        read();
    })

    watch(() => props.item.id, read)
    watch(() => times.meta_categories, () => cats.value = DM.getData("meta_categories"))
</script>