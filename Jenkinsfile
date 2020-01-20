pipeline {
  options {
    buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '15'))
  }
  agent { label 'singularity' }
  parameters {
    string(name: 'ogs', defaultValue: 'ufz/ogs@master',
           description: 'Build OGS in container (Github user/repo@branch)')
    string(name: 'format', defaultValue: 'docker',
           description: 'Container format, e.g.: docker singularity')
    string(name: 'openmpi_versions', defaultValue: 'off',
           description: 'OpenMPI versions, e.g.: off 2.1.2 2.1.5 3.0.1 3.1.2, ...')
    string(name: 'pm', defaultValue: 'system',
           description: 'Package manager to install third-party libs, e.g.: system conan')
    string(name: 'cmake', defaultValue: '',
           description: 'CMake args, have to be quoted and must start a space  e.g. "\' -DFOO=BAR\'"')
    //booleanParam(name: 'upload', defaultValue: false,
    //       description: 'Upload docker image to registry?')
    booleanParam(name: 'convert', defaultValue: true,
           description: 'Convert docker image to Singularity?')
    booleanParam(name: 'runtime', defaultValue: true,
           description: 'Create a runtime only image (contains just the built binaries and runtime dependencies)')
    booleanParam(name: 'deploy', defaultValue: false,
           description: 'Deploy Singularity images')
    string(name: 'other', defaultValue: '',
           description: 'Other parameter to the ogscm command, e.g. --base_image centos:7')
  }
  stages {
    stage('Build') {
      steps {
        script {
          upload = ""
          convert = ""
          runtime = ""
          cmake_args = ""
          //if (params.upload)
          //  upload = '--upload'
          if (params.convert)
            convert = '--convert'
          if (params.runtime)
            runtime = '--runtime-only'
          if (params.cmake != '')
            cmake_args = "--cmake_args ${params.cmake}"
          // BUG: credential not found
          //docker.withRegistry('https://registry.opengeosys.org', 'gitlab-bilke-api') {
            sh """
              python3 -m virtualenv ./venv
              . ./venv/bin/activate
              cat requirements.txt | xargs -n 1 -L 1 pip install
              alias singularity=`which singularity`
              export PYTHONPATH="\$PYTHONPATH:./"
              python ogscm/cli.py --build --format ${params.format} \
                --ogs ${params.ogs} --ompi ${params.openmpi_versions} \
                --pm ${params.pm} ${cmake_args} ${upload} \
                ${convert} ${runtime} ${params.other}
            """.stripIndent()
          //}
          if (params.deploy)
            sh """shopt -s globstar
                  cp -f _out/**/*.sif /var/images""".stripIndent()
        }
      }
    }
  }
  post {
    always {
      archiveArtifacts artifacts: '_out/**/*.sif,_out/**/*.def,_out/**/Dockerfile'
    }
    cleanup { sh 'rm -rf _out' }
  }
}

// Note: use input-step to deploy to HPC resource? https://stackoverflow.com/a/45216570/80480
