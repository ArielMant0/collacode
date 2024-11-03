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

        <div v-if="allowEdit" class="d-flex justify-space-between">
            <v-btn append-icon="mdi-delete"
                class="mt-2 mr-1"
                :disabled="!hasChanges"
                :color="hasChanges? 'error' : 'default'"
                @click="discard"
                >
                discard
            </v-btn>
            <v-btn append-icon="mdi-sync"
                class="mt-2 ml-1"
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
    import { createExtCategory, updateExtCategory } from '@/use/utility';
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

    const cats = ref([])

    const emit = defineEmits(["update", "cancel"])

    const hasChanges = computed(() => {
        return props.item.name !== name.value ||
            props.item.parent !== parent.value ||
            props.item.description !== desc.value
    })

    async function update() {

        if (!name.value) { return toast.error("missing name") }
        if (!desc.value) { return toast.error("missing description") }

        try {
            if (props.item.id) {
                props.item.name = name.value;
                props.item.description = desc.value;
                props.item.parent = parent.value;
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
                toast.success("created new externalization category")
            }
            emit("update")
            times.needsReload("ext_categories")
        } catch {
            toast.error("error creating new category")
        }
    }

    function discard() {
        if (hasChanges.value) {
            read();
        }
    }

    function read() {
        name.value = props.item.name
        desc.value = props.item.description
        parent.value = props.item.parent ? props.item.parent : null
    }

    onMounted(function() {
        cats.value = DM.getData("ext_categories")
        read();
    })

    watch(() => props.item.id, read)
    watch(() => times.ext_categories, () => cats.value = DM.getData("ext_categories"))
</script>