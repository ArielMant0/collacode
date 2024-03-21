<template>
    <div>
        <v-text-field v-model="tagName"
            class="mt-1"
            hide-details
            hide-spin-buttons
            label="Tag Name"
            :disabled="!props.data"
            density="compact"/>
        <v-textarea v-model="tagDesc"
            class="mt-1"
            hide-details
            hide-spin-buttons
            label="Tag Description"
            :disabled="!props.data"
            density="compact"/>

        <div class="d-flex justify-space-between">
            <v-btn append-icon="mdi-delete"
                class="mt-2 mr-1"
                :disabled="!props.data || !tagChanges"
                :color="tagChanges? 'error' : 'default'"
                @click="discard"
                >
                discard
            </v-btn>
            <v-btn append-icon="mdi-sync"
                class="mt-2 ml-1"
                :disabled="!props.data || !tagChanges"
                :color="tagChanges? 'secondary' : 'default'"
                @click="update"
                >
                sync
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
        }
    })

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
            loader.post("update/tags", { rows: [{
                id: props.data.id,
                name: tagName.value,
                description: tagDesc.value,
            }] })
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
        }
    }


    watch(props, read, { deep: true });
</script>