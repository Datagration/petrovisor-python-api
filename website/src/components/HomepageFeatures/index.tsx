import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  logo: string;
  description: ReactNode;
  linkUrl: string;
};

const FeatureList: FeatureItem[] = [
  {
    title: '.NET SDK',
    logo: '/petrovisor-python-api/img/logos/dotnet-logo.svg',
    description: (
      <>
        Advanced machine learning with our .NET C# SDK using ML.NET.
        Build intelligent applications for petroleum engineering workflows.
      </>
    ),
    linkUrl: 'https://www.nuget.org/packages/MyrConn.PetroVisor.Web.Client',
  },
  {
    title: 'R SDK',
    logo: '/petrovisor-python-api/img/logos/r-logo.svg',
    description: (
      <>
        Statistical analysis and visualization with our R language SDK.
        Built for statistical modeling and petroleum engineering workflows.
      </>
    ),
    linkUrl: 'https://github.com/Datagration/petrovisor-r-api',
  },
  {
    title: 'Python SDK',
    logo: '/petrovisor-python-api/img/logos/python-logo.svg',
    description: (
      <>
        Access PetroVisor platform capabilities with our Python SDK.
        Perfect for data science, engineering analysis, and automation.
      </>
    ),
    linkUrl: 'https://pypi.org/project/petrovisor/',
  },
];

function Feature({title, logo, description, linkUrl}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <Link to={linkUrl} className={styles.cardLink}>
        <div className={styles.featureCard}>
          <div className={styles.cardHeader}>
            <img src={logo} className={styles.featureLogo} alt={title} />
            <Heading as="h3">{title}</Heading>
          </div>
          <div className={styles.cardBody}>
            <p>{description}</p>
          </div>
        </div>
      </Link>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
