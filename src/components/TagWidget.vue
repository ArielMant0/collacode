<template>
    <div>
        <v-text-field v-model="tagName"
            class="mt-1"
            hide-details
            hide-spin-buttons
            :label="nameLabel"
            :disabled="!props.data || !props.canEdit"
            density="compact"/>
        <v-textarea v-model="tagDesc"
            class="mt-1"
            hide-details
            hide-spin-buttons
            :label="descLabel"
            :disabled="!props.data || !props.canEdit"
            density="compact"/>

        <div v-if="canEdit" class="d-flex justify-space-between">
            <v-btn append-icon="mdi-delete"
                class="mt-2 mr-1"
                :disabled="!props.data || !tagChanges"
                :color="tagChanges? 'error' : 'default'"
                @click="discard"
                >
                discard
            </v-btn>
            <v-btn :append-icon="buttonIcon"
                class="mt-2 ml-1"
                :disabled="!props.data || !tagChanges"
                :color="tagChanges? 'secondary' : 'default'"
                @click="update"
                >
                {{ props.buttonLabel }}
            </v-btn>
    </div>
    </div>
</template>

<script setup>
    import { ref, computed } from 'vue';
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
            tagName.value = props.data.name;
            tagDesc.value = props.data.description;
            emit("discard", props.data)
        }
    }


    watch(props, read, { deep: true });
</script>