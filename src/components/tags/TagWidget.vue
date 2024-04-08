<template>
    <div>
        <div class="d-flex mt-1">
            <v-text-field v-model="tagName"
                class="mr-1"
                hide-details
                hide-spin-buttons
                :label="nameLabel"
                :disabled="!data || !canEdit"
                density="compact"/>
            <v-text-field :model-value="tagCreator"
                hide-details
                hide-spin-buttons
                :label="creatorLabel"
                disabled
                density="compact"/>
        </div>
        <v-textarea v-model="tagDesc"
            class="mt-1"
            hide-details
            hide-spin-buttons
            :label="descLabel"
            :disabled="!data || !canEdit"
            density="compact"/>

        <div v-if="canEdit" class="d-flex justify-space-between">
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

    const loader = useLoader();
    const toast = useToast();
    const app = useApp();

    const props = defineProps({
        data: {
            type: Object,
            required: false
        },
        nameLabel: {
            type: String,
            default: "Tag Name"
        },
        creatorLabel: {
            type: String,
            default: "Tag Creator"
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
    })
    const emit = defineEmits(["update", "discard"])

    const tagName = ref("");
    const tagDesc = ref("");
    const tagCreator = computed(() => props.data ? app.getUserName(props.data.created_by) : "")
    const tagChanges = computed(() => {
        if (!props.data) {
            return false;
        }
        return props.data.name !== tagName.value ||
            props.data.description !== tagDesc.value;
    });

    function read() {
        tagName.value = props.data ? props.data.name : "";
        tagDesc.value = props.data ? props.data.description : "";
    }

    function update() {
        if (props.data && tagChanges) {
            const obj = {
                id: props.data.id,
                name: tagName.value,
                description: tagDesc.value,
                parent: props.data.parent === -1 ? null : props.data.parent,
                is_leaf: props.data.is_leaf,
            };
            emit("update", obj)
            if (props.emitOnly) return;

            loader.post("update/tags", { rows: [obj] })
                .catch(() => toast.error("invalid tag name or description"))
                .then(() => {
                    toast.success("updated tag " + tagName.value)
                    app.needsReload("tags")
                })
        }
    }
    function discard() {
        if (props.data) {
            tagName.value = props.data.name;
            tagDesc.value = props.data.description;
            emit("discard", props.data)
        }
    }

    onMounted(read)

    watch(props, read, { deep: true });
</script>