<template>
    <div>
        <v-text-field v-model="tagName"
            hide-details
            hide-spin-buttons
            :label="nameLabel"
            :disabled="!data"
            @update:model-value="change"
            density="compact"/>
        <v-text-field :model-value="tagCreator"
            class="mt-1"
            hide-details
            hide-spin-buttons
            :label="creatorLabel"
            disabled
            density="compact"/>

        <v-select v-model="tagParent"
            class="mt-1"
            hide-details
            hide-spin-buttons
            :label="parentLabel"
            :items="parentItems"
            :item-title="parentTitle"
            :item-value="parentValue"
            :disabled="!data"
            @update:model-value="change"
            density="compact">

            <template #prepend>
                <v-tooltip v-if="parentDesc" :text="parentDesc" location="top" open-delay="300">
                    <template v-slot:activator="{ props }">
                        <v-icon v-bind="props">mdi-help-circle-outline</v-icon>
                    </template>
                </v-tooltip>
            </template>
        </v-select>

        <v-textarea v-model="tagDesc"
            class="mt-1"
            hide-details
            hide-spin-buttons
            :label="descLabel"
            :disabled="!data"
            @update:model-value="change"
            density="compact"/>

        <div v-if="!noButtons" class="d-flex justify-space-between">
            <v-btn append-icon="mdi-delete"
                class="mt-2 mr-1"
                :disabled="!data || !tagChanges"
                :color="tagChanges? 'error' : 'default'"
                density="comfortable"
                variant="tonal"
                @click="discard"
                >
                discard
            </v-btn>

            <v-btn v-if="existing"
                append-icon="mdi-close"
                class="mt-2 mr-1"
                variant="tonal"
                density="comfortable"
                :color="allowEdit ? 'error' : 'default'"
                :disabled="!allowEdit"
                @click="remove"
                >
                delete
            </v-btn>

            <v-btn :append-icon="buttonIcon"
                class="mt-2 ml-1"
                variant="tonal"
                density="comfortable"
                :disabled="!allowEdit || !data || !tagChanges"
                :color="!allowEdit || !data || !tagChanges ? 'default' : 'secondary'"
                @click="update"
                >
                {{ buttonLabel }}
            </v-btn>
        </div>
    </div>
</template>

<script setup>
    import { ref, computed, onMounted } from 'vue';
    import { useApp } from '@/store/app';
    import { useToast } from 'vue-toastification';
    import DM from '@/use/data-manager';
    import { useTimes } from '@/store/times';
    import { addTags, deleteTags, updateTags } from '@/use/data-api';
    import { storeToRefs } from 'pinia';

    const app = useApp();
    const toast = useToast();
    const times = useTimes()

    const { allowEdit } = storeToRefs(app)

    const props = defineProps({
        data: {
            type: Object,
        },
        parents: {
            type: [Array, String],
            required: true
        },
        parentTitle: {
            type: String,
            default: "name"
        },
        parentValue: {
            type: String,
            default: "id"
        },
        nameLabel: {
            type: String,
            default: "Tag Name"
        },
        creatorLabel: {
            type: String,
            default: "Tag Creator"
        },
        parentLabel: {
            type: String,
            default: "Parent Tag"
        },
        descLabel: {
            type: String,
            default: "Tag Description"
        },
        buttonLabel: {
            type: String,
            default: "sync"
        },
        buttonIcon: {
            type: String,
            default: "mdi-sync"
        },
        emitOnly: {
            type: Boolean,
            default: false
        },
        noButtons: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["update", "change", "discard", "cancel"])

    const tagName = ref("");
    const tagDesc = ref("");
    const tagParent = ref(null);
    const parentDesc = ref("")
    const existing = computed(() => props.data && props.data.id !== undefined && props.data.id !== null)

    const tagCreator = computed(() => props.data ? app.getUserName(props.data.created_by) : "")
    const tagChanges = computed(() => {
        if (!props.data) {
            return false;
        }
        return props.data.name !== tagName.value ||
            props.data.description !== tagDesc.value ||
            (props.data.parent !== null && props.data.parent >= 0 && (tagParent.value === null || props.data.parent !== tagParent.value)) ||
            ((props.data.parent < 0 || props.data.parent === null) && tagParent.value !== null && tagParent.value > 0)
    });

    const parentItems = computed(() => {
        const obj = {}
        obj[props.parentTitle] = "<none>"
        obj[props.parentValue] = null

        const base = [obj]
        if (Array.isArray(props.parents)) {
            return base.concat(props.data && props.data.id ?
                props.parents.filter(d => d.id !== props.data.id) :
                props.parents);
        }
        return base.concat(props.data && props.data.id ?
            DM.getDataBy(props.parents, d => d.id !== props.data.id) :
            DM.getData(props.parents, false));
    })

    function read() {
        tagName.value = props.data ? props.data.name : "";
        tagDesc.value = props.data ? props.data.description : "";
        tagParent.value = props.data && props.data.parent !== -1 ? props.data.parent : null;
        parentDesc.value = props.data && props.data.parent !== -1 ? DM.getDataItem("tags_desc", props.data.parent) : null;
    }

    function change() {
        if (props.data && tagChanges.value) {
            emit("change", {
                id: props.data.id,
                name: tagName.value,
                description: tagDesc.value,
                parent: tagParent.value,
                is_leaf: props.data.is_leaf,
            })
        }
    }
    async function update() {
        if (props.data && tagChanges.value) {

            if (!tagName.value) {
                return toast.error("missing tag name")
            }

            const existing = parentItems.value.find(d => d[props.parentTitle] === tagName.value)
            if (existing) {
                return toast.error(`tag with name "${tagName.value}" already exists`)
            }

            const obj = {
                id: props.data.id,
                name: tagName.value,
                description: tagDesc.value,
                parent: tagParent.value,
                is_leaf: props.data.is_leaf !== undefined ? props.data.is_leaf : 1,
                code_id: app.currentCode
            };

            if (!props.emitOnly) {
                try {
                    if (obj.id) {
                        await updateTags([obj])
                        toast.success("updated tag " + tagName.value)
                    } else {
                        obj.code_id = app.currentCode
                        obj.created = Date.now()
                        obj.created_by = app.activeUserId
                        await addTags([obj])
                        toast.success("created tag " + tagName.value)
                    }
                    times.needsReload("tags")
                } catch {
                    toast.error("error updating/creating tag " + tagName.value)
                }
            }

            emit("update", obj)
        }
    }
    function discard() {
        if (props.data) {
            read();
            emit("discard", props.data)
        }
    }
    async function remove() {
        if (allowEdit.value && existing.value) {
            try {
                await deleteTags([props.data.id])
                toast.success("deleted tag " + props.data?.name)
                times.needsReload("tags")
                emit("cancel")
            } catch (e) {
                times.error("error deleting tag " + props.data?.name)
            }
        }
    }

    onMounted(read)

    watch(() => props.data?.id, read);
    watch(() => props.parents, read, { deep: true });
    watch(() => Math.max(times.tags, times.tags_old, times.tagging), read)
</script>