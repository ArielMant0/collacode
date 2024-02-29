<template>
    <div>
        <v-dialog v-model="model" width="auto">
            <v-card max-width="500" prepend-icon="mdi-login" title="Who are you?" persistent>
                <template v-slot:text>
                    <v-list select-strategy="single-leaf" v-model:selected="selected">
                        <v-list-item v-for="user in users"
                            :key="user.id"
                            :title="user.name"
                            :subtitle="user.role"
                            :value="user.id"
                            density="compact"
                            class="pr-2 pl-2 pt-1 pb-1"
                            hide-details>

                            <template v-slot:prepend>
                                <v-card size="small"
                                    density="comfortable"
                                    elevation="0"
                                    rounded="circle"
                                    class="pa-1 mr-4 d-flex"
                                    :color="user.color">
                                    <v-icon color="white">mdi-account</v-icon>
                                </v-card>
                            </template>
                        </v-list-item>
                    </v-list>
                </template>

                <template v-slot:actions>
                    <v-btn class="ms-auto"
                        text="Confirm"
                        :disabled="selected.length === 0"
                        @click="emit('select', selected[0])"></v-btn>
                </template>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>
    import { ref } from 'vue';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';

    const selected = ref([]);
    const model = defineModel({ type: Boolean, required: true })
    const app = useApp();

    const { users } = storeToRefs(app);
    const emit = defineEmits(["select"])
</script>