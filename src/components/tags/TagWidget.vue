<template>
    <div>
        <v-text-field v-model="tagName"
            hide-details
            hide-spin-buttons
            :label="nameLabel"
            :disabled="!data || !canEdit"
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
            :disabled="!data || !canEdit"
            @update:model-value="change"
            density="compact"/>
        <v-textarea v-model="tagDesc"
            class="mt-1"
            hide-details
            hide-spin-buttons
            :label="descLabel"
            :disabled="!data || !canEdit"
            @update:model-value="change"
            density="compact"/>

        <div v-if="canEdit && !noButtons" class="d-flex justify-space-between">
            <v-btn append-icon="mdi-delete"
                class="mt-2 mr-1"
                :disabled="!data || !tagChanges"
                :color="tagChanges? 'error' : 'default'"
                @click="discard"
                >
                discard
            </v-btn>
            <v-btn :append-icon="buttonIcon"
                class="mt-2 ml-1"
                :disabled="!data || !tagChanges"
                :color="tagChanges? 'secondary' : 'default'"
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
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import DM from '@/use/data-manager';

    const loader = useLoader();
    const toast = useToast();
    const app = useApp();

    const props = defineProps({
        data: {
            type: Object,
            required: false
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
        canEdit: {
            type: Boolean,
            default: false
        },
        noButtons: {
            type: Boolean,
            default: false
        },
    })
    const emit = defineEmits(["update", "change", "discard"])

    const tagName = ref("");
    const tagDesc = ref("");
    const tagParent = ref(null);
    const tagCreator = computed(() => props.data ? app.getUserName(props.data.created_by) : "")
    const tagChanges = computed(() => {
        if (!props.data) {
            return false;
        }
        return props.data.name !== tagName.value ||
            props.data.description !== tagDesc.value ||
            props.data.parent !== tagParent.value;
    });

    const parentItems = computed(() => {
        if (Array.isArray(props.parents)) {
            return props.data && props.data.id ?
                props.parents.filter(d => d.id !== props.data.id) :
                props.parents;
        }
        return props.data && props.data.id ?
            DM.getDataBy(props.parents, d => d.id !== props.data.id) :
            DM.getData(props.parents, false);
    })

    function read() {
        tagName.value = props.data ? props.data.name : "";
        tagDesc.value = props.data ? props.data.description : "";
        tagParent.value = props.data && props.data.parent !== -1 ? props.data.parent : null;
    }

    function change() {
        if (props.data && tagChanges) {
            emit("change", {
                id: props.data.id,
                name: tagName.value,
                description: tagDesc.value,
                parent: tagParent.value,
                is_leaf: props.data.is_leaf,
            })
        }
    }
    function update() {
        if (props.data && tagChanges) {
            console.log(tagParent.value)
            const obj = {
                id: props.data.id,
                name: tagName.value,
                description: tagDesc.value,
                parent: tagParent.value,
                is_leaf: props.data.is_leaf,
            };
            emit("update", obj)
            if (props.emitOnly) return;

            loader.post("update/tags", { rows: [obj] })
                .then(() => {
                    toast.success("updated tag " + tagName.value)
                    app.needsReload("tags")
                })
                .catch(() => toast.error("invalid tag name or description"))
        }
    }
    function discard() {
        if (props.data) {
            read();
            emit("discard", props.data)
        }
    }

    onMounted(read)

    watch(props, read, { deep: true });
</script>