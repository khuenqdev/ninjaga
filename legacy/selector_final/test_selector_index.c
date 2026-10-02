#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <dlfcn.h>
#include <stdbool.h>
#include <stdlib.h>

typedef bool(*E)(unsigned,void*); typedef void(*V)(const void*,unsigned,unsigned,size_t); typedef void(*A)(int16_t,int16_t); typedef size_t(*B)(const int16_t*,size_t); typedef void(*P)(void); typedef int16_t(*S)(unsigned,unsigned,unsigned,unsigned); typedef struct{const char*path;const void*data;size_t size;const char*meta;} GI;
static int btn[16]; static uint8_t *ram; static unsigned f;
static bool env(unsigned c,void*d){ if(c==10){*(unsigned*)d=1;return true;} if(c==8||c==11||c==37)return true; return false; }
static void vid(const void*d,unsigned w,unsigned h,size_t p){(void)d;(void)w;(void)h;(void)p;} static void aud(int16_t a,int16_t b){(void)a;(void)b;} static size_t ab(const int16_t*d,size_t n){(void)d;return n;} static void poll(void){}
static int16_t st(unsigned p,unsigned d,unsigned i,unsigned id){(void)i;return p==0&&d==1&&id<16?btn[id]:0;}
int main(int ac,char**av){if(ac<3)return 2;int target=strtol(av[2],0,0);void*h=dlopen("/mnt/data/fceumm_libretro.so",RTLD_NOW);if(!h){perror("dlopen");return 1;}typedef void(*F)(void);typedef void(*SE)(E);typedef void(*SV)(V);typedef void(*SA)(A);typedef void(*SB)(B);typedef void(*SP)(P);typedef void(*SI)(S);typedef bool(*LG)(const GI*);typedef void*(*GM)(unsigned);F ri=dlsym(h,"retro_init"),rr=dlsym(h,"retro_run");SE re=dlsym(h,"retro_set_environment");SV rv=dlsym(h,"retro_set_video_refresh");SA ra=dlsym(h,"retro_set_audio_sample");SB rab=dlsym(h,"retro_set_audio_sample_batch");SP rp=dlsym(h,"retro_set_input_poll");SI rs=dlsym(h,"retro_set_input_state");LG lg=dlsym(h,"retro_load_game");GM gm=dlsym(h,"retro_get_memory_data");re(env);rv(vid);ra(aud);rab(ab);rp(poll);rs(st);ri();GI gi={av[1],0,0,0};if(!lg(&gi))return 3;ram=gm(2);for(f=0;f<1800;f++){memset(btn,0,sizeof(btn));if(f==780)btn[3]=1;if(f>=900&&f<905)btn[2]=1;for(int n=1;n<=target;n++)if(f>=900+20*n&&f<905+20*n)btn[7]=1;if(f==1200)btn[3]=1;rr();if(f==900||f==920||f==940||f==1000||f==1140||f==1160||f==1200||f==1230||f==1260||f==1320||f==1440||f==1600)printf("idx=%d f=%04u state=%02x 28=%02x 29=%02x 0a=%02x 0b=%02x 300=%02x 303=%02x 6d=%02x\n",target,f,ram[0x7ff],ram[0x28],ram[0x29],ram[0x0a],ram[0x0b],ram[0x300],ram[0x303],ram[0x6d]);}return 0;}
